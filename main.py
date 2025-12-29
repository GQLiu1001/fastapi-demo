from fastapi import FastAPI,Path,Query
from pydantic import BaseModel
app = FastAPI()

# region 路径参数
# @app.方法("请求路径")
# @app.方法("{路径参数}")
# 限制路径参数的方法
@app.get("/hi/{id}")
# endregion
# region Path
# Path(...) 三个点代表必填
# Path(...,gt=0,le=101) 必填，大于0 小于等于101
# Path(...,gt=0,le=101,description="ID") 必填，大于0 小于等于101 描述
# Path(...,min_length=3,description="名字")) 必填，长度范围 min/max_length
# endregion
async def hi(id: int = Path(...,gt=0,le=101,description="ID")):
    return {"id":id}
@app.get("/hii/{name}")
async def hii(name: str = Path(...,min_length=3,description="名字")):
    return {"name":name}
# region 请求参数
# 直接写 用等号赋值默认值
# 用 Query() 限制
# Query(0,ge=0) 非必须 默认0 大于0
@app.get("/hiii")
async def hiii(
        skip:int = Query(0,ge=0,description="跳过的记录数") ,
        limit:int =100
):
    return {"skip":skip,"limit":limit}
# endregion
# region 请求体
class Student(BaseModel):
    name: str
    age: int

# endregion
@app.get("/")
async def root():
    return {"message": "Hello World"}
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
@app.get("/hello")
async def my_hello():
    return {"message": "Hello World Hello"}
