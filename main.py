import random
from typing import Generic, TypeVar, Optional

from fastapi import FastAPI, Path, Query, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse, FileResponse

app = FastAPI()

# region 路径参数
# @app.方法("请求路径")
# @app.方法("{路径参数}")
# 限制路径参数的方法
@app.get("/path-variable/{id}")
async def hi(id: int = Path(...,gt=0,le=101,description="ID")):
    return {"id":id}
# endregion

# region Path()
# Path(...) 三个点代表必填
# Path(...,gt=0,le=101) 必填，大于0 小于等于101
# Path(...,gt=0,le=101,description="ID") 必填，大于0 小于等于101 描述
# Path(...,min_length=3,description="名字")) 必填，长度范围 min/max_length
@app.get("/path-variable/{name}")
async def hii(name: str = Path(...,min_length=3,description="名字")):
    return {"name":name}
# endregion

# region Query()
# 直接写 用等号赋值默认值
# 用 Query() 限制
# Query(0,ge=0) 非必须 默认0 大于0
# endregion

# region 请求参数
@app.get("/request-param")
async def hiii(
        skip:int = Query(0,ge=0,description="跳过的记录数") ,
        limit:int =100
):
    return {"skip":skip,"limit":limit}
# endregion

# region Field()


# region 实体类
class Student(BaseModel):
    name: str = Field(...,max_length=3,description="学生姓名")
    age: int = Field(...,gt=3,description="学生年纪 大于3")
# endregion


# region 请求体
@app.post("/request-body")
async def request_student(student: Student):
    return {"name":student.name,"age":student.age}
# endregion

# region 响应类型
# JSONResponse 自动转换
#    return{"key":"value"}
# HTMLResponse
#    return HTMLResponse(html_content)
@app.get("/html")
async def get_html():
    return HTMLResponse("<h1>html_content</h1>")

# FileResponse
#    return FileResponse(file)
@app.get("/file")
async def get_file():
    return FileResponse("gojo-jujutsu.jpg")
# endregion

# region 自定义相应格式
# 首先需要创建一个基于 pydantic 的实体类
# 定义类型变量T（名称可自定义，通常用T、U等大写字母表示）
# bound=BaseModel（可选）：限制T只能是BaseModel的子类（仅业务实体类），不写则支持任意类型
T = TypeVar('T')
# 若需无约束（支持任意类型：dict、list、int、自定义类等），直接写：T = TypeVar('T')
# T = TypeVar('T', bound=BaseModel)  # 带约束的类型变量
class Results(BaseModel, Generic[T]):
    # 原有固定字段
    code: int = Field(..., description="响应状态码：200成功，500服务器错误")
    message: str = Field(..., description="响应提示信息")
    # 泛型data字段：类型为T（动态指定），允许为None
    data: Optional[T] = Field(None, description="泛型业务数据，支持任意指定类型")

class News(BaseModel):
    id:int
    title:str
    content:str
@app.get("/news/{id}",response_model=News)
async def new_news(id: int):
    return {
        "id":id,
        "title":f"这是{id}",
        "content":"hello"
    }
# endregion

# region exception
# HTTPException
@app.get("/exception401")
async def exception401():
    # # 1. 获取指定整数范围的随机数：[1, 10]（包含首尾）
    # random.randint(1, 10)
    # # 2. 从列表中随机选取一个元素
    # random.choice(["a", "b", "c"])
    # # 3. 获取指定范围的随机浮点数：[1.0, 10.0]
    # random.uniform(1.0, 10.0)
    # 调用random.random()获取0.0~1.0的随机浮点数
    if random.random() > 0.5:
        # 注意：if语句块内的代码需要缩进（4个空格/1个Tab），否则语法错误
        raise HTTPException(status_code=401, detail="报错咯")
    # 若不满足条件，返回正常响应
    return {"code": 200, "message": "请求成功", "data": None}