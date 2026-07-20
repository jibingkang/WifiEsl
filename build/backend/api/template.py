"""
模板管理API - 模板CRUD (从数据库读写)
GET    /api/v1/templates          - 获取模板列表(含字段定义)
GET    /api/v1/templates/:id       - 获取单个模板详情
POST   /api/v1/templates          - 创建新模板
POST   /api/v1/templates/sync     - 从WIFI系统同步模板
PUT    /api/v1/templates/:id       - 更新模板
DELETE /api/v1/templates/:id       - 删除模板
GET    /api/v1/update-history      - 更新历史记录(分页)
"""
import logging
from fastapi import APIRouter, Request, HTTPException, Query

from services.db_service import (
    get_all_templates,
    get_template_by_tid,
    create_template,
    update_template,
    delete_template,
    sync_template_from_remote,
    get_logs,
    get_db as _get_tpl_db,
)
from services.auth_service import get_current_user_id_from_token
from services.db_service_extended import get_user_by_id
from services.wifi_client import wifi_proxy
from services.wifi_connection_manager import wifi_connection_manager

router = APIRouter(prefix="/templates", tags=["模板管理"])
logger = logging.getLogger(__name__)


@router.get("")
async def get_template_list(request: Request):
    """获取可用模板列表 (含字段定义)"""
    templates = await get_all_templates()
    # 转换为前端期望的格式
    data = []
    for t in templates:
        fields = []
        for f in t.get("fields", []):
            fields.append({
                "key": f["field_key"],
                "label": f["field_label"],
                "type": f["field_type"],
                "required": f["required"],
                "default_value": f["default_value"] or None,
                "placeholder": f["placeholder"] or None,
                "options": f.get("options", []),
                "order": f["sort_order"],
            })
        data.append({
            "tid": t["tid"],
            "tname": t["tname"],
            "description": t.get("description") or "",
            "screen_type": t.get("screen_type") or None,
            "image": t.get("image") or None,
            "screen_width": t.get("screen_width") or 0,
            "screen_height": t.get("screen_height") or 0,
            "remote_updated_at": t.get("remote_updated_at") or "",
            "fields": fields,
        })
    return {"code": 20000, "message": "", "data": data}


@router.get("/{template_id}")
async def get_template_detail(template_id: str, request: Request):
    """获取单个模板详情"""
    tpl = await get_template_by_tid(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")

    fields = []
    for f in tpl.get("fields", []):
        fields.append({
            "key": f["field_key"],
            "label": f["field_label"],
            "type": f["field_type"],
            "required": f["required"],
            "default_value": f["default_value"] or None,
            "placeholder": f["placeholder"] or None,
            "options": f.get("options", []),
            "order": f["sort_order"],
        })

    return {
        "code": 20000,
        "message": "",
        "data": {
            "tid": tpl["tid"],
            "tname": tpl["tname"],
            "description": tpl.get("description") or "",
            "screen_type": tpl.get("screen_type"),
            "fields": fields,
        },
    }


@router.post("")
async def create_new_template(request: dict):
    """
    创建新模板 (手动添加)
    Body: { tid, tname, description?, screen_type?, fields?: [...] }
    fields 中每个元素: { key, label, type, required?, default_value?, placeholder?, options? }
    """
    body = request if isinstance(request, dict) else {}
    try:
        tid = body.get("tid")
        tname = body.get("tname")
        if not tid or not tname:
            raise HTTPException(status_code=400, detail="tid 和 tname 必填")

        tpl_id = await create_template(
            tid=tid,
            tname=tname,
            description=body.get("description", ""),
            screen_type=body.get("screen_type", ""),
            fields=body.get("fields"),
        )
        logger.info(f"创建模板成功: {tid} (id={tpl_id})")
        return {"code": 20000, "message": "模板创建成功", "data": {"id": tpl_id}}
    except Exception as e:
        logger.error(f"创建模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}")
async def update_existing_template(template_id: str, request: dict):
    """
    更新模板信息或字段定义
    Body 可包含: { tname?, description?, screen_type?, fields?: [...] }
    传入 fields 会替换全部字段（不传则保留原字段）
    """
    body = request if isinstance(request, dict) else {}
    try:
        await update_template(tid=template_id, **body)
        logger.info(f"更新模板成功: {template_id}")
        return {"code": 20000, "message": "模板已更新", "data": None}
    except Exception as e:
        logger.error(f"更新模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def remove_template(template_id: str, request: Request):
    """删除模板"""
    try:
        await delete_template(template_id)
        logger.info(f"删除模板成功: {template_id}")
        return {"code": 20000, "message": "模板已删除", "data": None}
    except Exception as e:
        logger.error(f"删除模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── 从WIFI系统同步模板 ──

@router.post("/sync")
async def sync_templates(request: Request):
    """
    从WIFI系统拉取模板列表和详情，自动同步到本地数据库。
    自动解析模板的 fabric.js 数据，提取动态字段。
    """
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
    user_id = get_current_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="未授权")

    # 获取用户的 WIFI 连接信息
    conn = await wifi_connection_manager.get_connection(user_id)
    if not conn or not conn.token:
        raise HTTPException(status_code=401, detail="请先在设备管理页面连接WIFI系统")

    api_key = conn.token
    base_url = conn.wifi_base_url

    try:
        # 1. 获取模板列表
        template_list = await wifi_proxy.list_templates(api_key, base_url)
        if not template_list:
            return {"code": 20000, "message": "WIFI系统没有模板", "data": {"synced": 0, "failed": 0}}

        synced = 0
        failed = 0

        # 2. 遍历每个模板，获取详情并同步
        for item in template_list:
            tpl_id = item.get("_id") or item.get("id", "")
            if not tpl_id:
                failed += 1
                continue

            try:
                detail = await wifi_proxy.get_template_detail(tpl_id, api_key, base_url)
                if not detail:
                    failed += 1
                    continue

                tname = detail.get("name", tpl_id)
                fabric_data = detail.get("data", "{}")
                image_url = detail.get("image", "")
                remote_updated_at = detail.get("updatedAt", "")

                await sync_template_from_remote(tpl_id, tname, fabric_data, image_url, remote_updated_at)
                synced += 1
            except Exception as e:
                logger.error(f"[模板同步] 同步模板 {tpl_id} 失败: {e}")
                failed += 1

        logger.info(f"[模板同步] 完成: 成功 {synced}, 失败 {failed}")
        return {
            "code": 20000,
            "message": f"同步完成: 成功 {synced} 个, 失败 {failed} 个",
            "data": {"synced": synced, "failed": failed},
        }

    except Exception as e:
        logger.error(f"[模板同步] 同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


# ── 更新历史记录 ──

history_router = APIRouter(prefix="/update-history", tags=["更新历史"])


@history_router.get("")
async def get_update_history_api(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
):
    """分页查询批量更新历史记录（按家族树权限过滤）"""
    # 获取当前用户信息
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
    user_id = get_current_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="未授权")

    # 计算权限范围
    from api.logs import get_family_tree_ids as _get_history_tree, _build_allowed_user_ids as _build_hist_allowed
    _h_db = await _get_tpl_db()
    user_info = await get_user_by_id(user_id)
    role = user_info.get("role", "user") if user_info else "user"
    allowed = await _build_hist_allowed(_h_db, user_id, role)

    items, total = await get_logs(
        page=page,
        page_size=pageSize,
        action=["task_push", "batch_update_template"],
        allowed_user_ids=allowed,
    )
    return {
        "code": 20000,
        "message": "",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": pageSize,
        },
    }
