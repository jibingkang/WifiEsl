"""Fix tasks.py: add mutex lock + proper indentation, using original as base."""
# Step 1: Apply import and lock changes
with open('backend/api/tasks_orig.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_import = '''from services.wifi_client import wifi_proxy
from services.auth_service import get_current_user_id_from_token
from services.wifi_connection_manager import wifi_connection_manager

router = APIRouter(prefix="/tasks", tags=["更新任务"])
logger = logging.getLogger(__name__)'''

new_import = '''from services.wifi_client import wifi_proxy
from services.auth_service import get_current_user_id_from_token
from services.wifi_connection_manager import wifi_connection_manager

router = APIRouter(prefix="/tasks", tags=["更新任务"])
logger = logging.getLogger(__name__)

# 任务推送互斥锁：防止同一任务被同时多次推送
_task_push_locks: dict[int, asyncio.Lock] = {}


async def _get_task_push_lock(task_id: int) -> asyncio.Lock:
    """获取指定任务的推送锁（惰性创建）"""
    if task_id not in _task_push_locks:
        _task_push_locks[task_id] = asyncio.Lock()
    return _task_push_locks[task_id]'''

content = content.replace(old_import, new_import)

old_body = '''    wifi_token, wifi_base_url = await _get_wifi_config(request)
    if not wifi_token:
        raise HTTPException(status_code=401, detail="未授权")

    # 解析 default_data'''

new_body = '''    wifi_token, wifi_base_url = await _get_wifi_config(request)
    if not wifi_token:
        raise HTTPException(status_code=401, detail="未授权")

    # 获取任务推送互斥锁，防止同一任务重复推送
    push_lock = await _get_task_push_lock(task_id)
    async with push_lock:
        logger.info(f"[Task-{task_id}] 获取推送锁，开始执行推送")

        # 解析 default_data'''

content = content.replace(old_body, new_body)

# Save intermediate file
with open('backend/api/tasks_stage1.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Step 2: Fix indentation for async with block
with open('backend/api/tasks_stage1.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

async_idx = None
return_idx = None

for i, line in enumerate(lines):
    if 'async with push_lock:' in line and async_idx is None:
        async_idx = i
        async_indent = len(line) - len(line.lstrip())

# Find the end of execute_task_push function (return at same indent as async with)
# Function ends at the return statement that matches async with's indent
for i in range(len(lines)-1, async_idx, -1):
    stripped = lines[i].lstrip()
    cur_indent = len(lines[i]) - len(stripped)
    if stripped.startswith('return {') and cur_indent == async_indent:
        return_idx = i
        break

print(f"async_with line={async_idx+1}, return line={return_idx+1}")

# Build output with proper indentation
result = []
for i, line in enumerate(lines):
    if i <= async_idx:
        result.append(line)
    elif async_idx < i < return_idx:
        if line.strip():
            result.append('    ' + line)
        else:
            result.append('    \n')
    else:
        result.append(line)

with open('backend/api/tasks.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

print("Fixed tasks.py")
