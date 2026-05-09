"""
模板管理API - 模板CRUD (从数据库读写)
GET    /api/v1/templates          - 获取模板列表(含字段定义)
GET    /api/v1/templates/:id       - 获取单个模板详情
POST   /api/v1/templates          - 创建新模板
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
    get_logs,
    get_db as _get_tpl_db,
)
from services.auth_service import get_current_user_id_from_token
from services.db_service_extended import get_user_by_id

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
        action="batch_update_template",
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
