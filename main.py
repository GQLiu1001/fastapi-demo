import random
import time
from platform import system
from typing import Generic, TypeVar, Optional
import datetime
from fastapi import FastAPI, Path, Query, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, func, String, Float, select, desc, asc
from sqlalchemy.ext.asyncio import  create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.requests import Request
from starlette.responses import HTMLResponse, FileResponse

app = FastAPI()

# region 中间件
# 也就是 拦截器
@app.middleware("http")
async def middleware1(request: Request,call_next):
    # 请求响应前的逻辑代码
    print("中间件1 start")
    # time.sleep(2)
    print("检查token通过")
    # await 后面放要异步执行的代码
    # 把 request 传下去 -> 进入下面的 middleware2 获取返回
    res = await call_next(request)
    print("中间件1 end")


    # 经过中间件后 响应给客户端
    return res

@app.middleware("http")
async def middleware2(request: Request,call_next):
    # 请求响应前的逻辑代码
    print("中间件2 start")
    # time.sleep(2)
    print("检查权限通过")
    # await 后面放要异步执行的代码
    # 把 request 传下去
    res = await call_next(request)
    print("中间件2 end")

    # 经过中间件后 响应给客户端
    return res
# endregion

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
# endregion

# region Depends 依赖注入
# 1.定义通用的依赖项
async def common_param(
    skip:int = Query(0, ge=0),
    limit:int = Query(10, le=100),
):
    return {"skip":skip,"limit":limit}
# 2.导入 Depends
# 3.注入
@app.get("/news-list",response_model=News)
async def news_list(commons = Depends(common_param)):
    return {
        "id":3,
        "title":f"这是{commons}",
        "content":"hello"
    }

# endregion

# region orm 建表
# 用的
# pip install aiomysql
# pip install sqlalchemy[asyncio]
ASYNC_DATABASE_URL = "mysql+aiomysql://root:123123@localhost:3306/fastapi_test?charset=utf8"
# 1.创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # 输出SQL日志
    pool_size=10,
    max_overflow=15,
)

# 2. 定义模型类: 基类 + 表对应的模型类
# 基类: 创建时间、更新时间; 书籍表: id、书名、作者、价格、出版社
class Base(DeclarativeBase):
    create_time: Mapped[datetime] = (
        mapped_column(
            DateTime,
            insert_default=func.now(),
            default=func.now,
            comment="创建时间"
        )
    )
    update_time: Mapped[datetime] = (
        mapped_column(
            DateTime,
            insert_default=func.now(),
            default=func.now,
            onupdate=func.now(),
            comment="更新时间"
        )
    )
class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True, comment="书籍id")
    bookname: Mapped[str] = mapped_column(String(255), comment="书名")
    author: Mapped[str] = mapped_column(String(255), comment="作者")
    price: Mapped[float] = mapped_column(Float, comment="价格")
    publisher: Mapped[str] = mapped_column(String(255), comment="出版社")

# 3. 建表
async def create_tables():
    # 获取异步引擎
    async with async_engine.begin() as conn:
        # 使用模型类基类创建
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup():
    await create_tables()
# endregion

# region 异步会话工厂
# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,  # 绑定数据库引擎
    class_=AsyncSession,  # 指定会话类
    expire_on_commit=False  # 会话对象不过期，不重新查询数据库
)


# 依赖项，用于获取数据库会话
async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # 返回数据库会话给路由处理函数
            await session.commit()  # 无异常，提交事务
        except Exception:
            await session.rollback()  # 有异常则回滚
            raise
        finally:
            await session.close()  # 关闭会话
# endregion

# region 查询
# 路由匹配中使用ORM的接口
@app.get("/book/books/{book_id}")
async def get_book_list(
    book_id:int,
    db: AsyncSession = Depends(get_database) # 注入数据库会话
):
    # 查询所有书籍
    # result = await db.execute(select(Book))  # Book是你的书籍模型类 返回一个 ORM 对象
    # result = await db.execute(select(Book).where(Book.id>3))
    result = await db.execute(
        select(Book)
        .where(Book.id>book_id)
        .where(Book.price>100)
    )
    # scalars().first() 获取第一条 scalars 对 ORM 对象进行操作
    # books = result.scalars().first()
    # scalars().all() 获取所有
    books = result.scalars().all()
    # db.get(Book,3) 获取 Book 的 id(主键) 为 3 的书 获取单条数据
    # books = await db.get(Book,3)
    return books
# -------------------------- ORM 基本查询场景全覆盖（核心代码） --------------------------
@app.get("/book/by-id/{book_id}", summary="1. 主键查询（单条数据，最常用）")
async def get_book_by_primary_key(
        book_id: int = Path(..., gt=0, description="书籍主键ID"),
        db: AsyncSession = Depends(get_database)
):
    # 方式1：db.get(模型类, 主键值) - 最简主键查询（推荐）
    book = await db.get(Book, book_id)
    # 方式2：等价于 select + where + first()（显式条件查询单条）
    # result = await db.execute(select(Book).where(Book.id == book_id))
    # book = result.scalars().first()

    if not book:
        return {"code": 404, "message": "书籍不存在", "data": None}
    return {"code": 200, "message": "查询成功", "data": book}


@app.get("/book/all", summary="2. 无条件查询（所有数据）")
async def get_all_books(
        db: AsyncSession = Depends(get_database)
):
    # 无条件查询所有书籍，scalars().all() 返回列表
    result = await db.execute(select(Book))
    books = result.scalars().all()
    return {"code": 200, "message": f"共查询到 {len(books)} 本图书", "data": books}


@app.get("/book/by-single-condition/{min_price}", summary="3. 单条件查询（所有符合条件数据）")
async def get_books_by_single_condition(
        min_price: float = Path(..., ge=0, description="最低价格"),
        db: AsyncSession = Depends(get_database)
):
    # 单个where条件：价格 >= 最低价格
    result = await db.execute(select(Book).where(Book.price >= min_price))
    books = result.scalars().all()
    return {"code": 200, "message": f"价格≥{min_price} 的图书共 {len(books)} 本", "data": books}


@app.get("/book/by-multi-conditions/{book_id}/{min_price}", summary="4. 多条件查询（你的原有场景）")
async def get_books_by_multi_conditions(
        book_id: int = Path(..., gt=0, description="书籍ID阈值"),
        min_price: float = Path(..., ge=0, description="最低价格阈值"),
        db: AsyncSession = Depends(get_database)
):
    # 方式1：多个where链式调用（逻辑与 AND）
    result = await db.execute(
        select(Book)
        .where(Book.id > book_id)
        .where(Book.price > min_price)
    )
    # 方式2：单个where内用逗号分隔（等价于 AND，更简洁）
    # result = await db.execute(
    #     select(Book).where(Book.id > book_id, Book.price > min_price)
    # )
    # 方式3：显式使用 and_（复杂条件推荐）
    # from sqlalchemy import and_
    # result = await db.execute(
    #     select(Book).where(and_(Book.id > book_id, Book.price > min_price))
    # )

    books = result.scalars().all()
    return {"code": 200, "message": f"ID>{book_id} 且 价格>{min_price} 的图书共 {len(books)} 本", "data": books}


@app.get("/book/by-condition-single/{book_name}", summary="5. 条件查询（单条数据，取第一条匹配结果）")
async def get_book_single_by_condition(
        book_name: str = Path(..., description="书籍名称（模糊匹配）"),
        db: AsyncSession = Depends(get_database)
):
    # 模糊查询：bookname 包含指定字符串（like），scalars().first() 取第一条
    result = await db.execute(select(Book).where(Book.bookname.like(f"%{book_name}%")))
    book = result.scalars().first()  # 仅返回第一条匹配数据，无结果返回None

    if not book:
        return {"code": 404, "message": f"未找到包含「{book_name}」的书籍", "data": None}
    return {"code": 200, "message": "查询成功", "data": book}


@app.get("/book/order-by/{sort_field}", summary="6. 排序查询（升序/降序）")
async def get_books_with_sort(
        sort_field: str = Path(..., description="排序字段（id/price）"),
        is_desc: bool = True,  # 是否降序（True=降序，False=升序）
        db: AsyncSession = Depends(get_database)
):
    # 构建排序条件
    if sort_field == "id":
        order_by_clause = desc(Book.id) if is_desc else asc(Book.id)
    elif sort_field == "price":
        order_by_clause = desc(Book.price) if is_desc else asc(Book.price)
    else:
        return {"code": 400, "message": "仅支持 id/price 字段排序", "data": None}

    # 排序查询
    result = await db.execute(select(Book).order_by(order_by_clause))
    books = result.scalars().all()
    sort_type = "降序" if is_desc else "升序"
    return {"code": 200, "message": f"按 {sort_field} {sort_type} 排序，共 {len(books)} 本图书", "data": books}


@app.get("/book/page", summary="7. 分页查询（常用列表分页）")
async def get_books_with_pagination(
        page: int = 1,  # 当前页码（默认第1页）
        page_size: int = 10,  # 每页条数（默认10条）
        db: AsyncSession = Depends(get_database)
):
    if page < 1 or page_size < 1:
        return {"code": 400, "message": "页码和每页条数必须大于0", "data": None}

    # 计算偏移量：offset = (当前页码-1) * 每页条数
    offset = (page - 1) * page_size
    # 分页查询：offset（跳过条数） + limit（获取条数）
    result = await db.execute(select(Book).offset(offset).limit(page_size))
    books = result.scalars().all()

    # 可选：查询总条数（用于计算总页数）
    count_result = await db.execute(select(func.count(Book.id)))
    total = count_result.scalar_one()  # 获取总条数
    total_pages = (total + page_size - 1) // page_size  # 向上取整计算总页数

    return {
        "code": 200,
        "message": "分页查询成功",
        "data": {
            "list": books,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            }
        }
    }
# endregion

# region 增删改
# 第一步：先定义书籍新增/修改的Pydantic入参模型（与ORM模型解耦，更安全）
class BookCreate(BaseModel):
    """书籍新增入参模型（无需id，主键自增）"""
    bookname: str = Field(..., max_length=255, description="书名")
    author: str = Field(..., max_length=255, description="作者")
    price: float = Field(..., gt=0, description="价格（大于0）")
    publisher: str = Field(..., max_length=255, description="出版社")


class BookUpdate(BaseModel):
    """书籍修改入参模型（字段可选，支持部分更新）"""
    bookname: Optional[str] = Field(None, max_length=255, description="书名")
    author: Optional[str] = Field(None, max_length=255, description="作者")
    price: Optional[float] = Field(None, gt=0, description="价格（大于0）")
    publisher: Optional[str] = Field(None, max_length=255, description="出版社")


# -------------------------- 一、新增操作（C：Create） --------------------------
@app.post("/book/create", summary="1. 新增单条书籍数据", response_model=Results[Book])
async def create_single_book(
        book_info: BookCreate,
        db: AsyncSession = Depends(get_database)
):
    # 1. 将Pydantic入参转换为ORM模型实例
    new_book = Book(
        bookname=book_info.bookname,
        author=book_info.author,
        price=book_info.price,
        publisher=book_info.publisher
    )
    # 2. 添加到数据库会话
    db.add(new_book)
    # 3. 提交事务（会自动生成主键id）
    await db.flush()  # 刷新会话，获取自增主键（无需等待commit，更快获取id）
    await db.commit()
    # 4. 刷新实例，获取完整数据（包含create_time/update_time）
    await db.refresh(new_book)

    return Results[Book](
        code=200,
        message="书籍新增成功",
        data=new_book
    )


@app.post("/book/create/batch", summary="2. 批量新增书籍数据", response_model=Results[list[Book]])
async def create_batch_books(
        book_list: list[BookCreate],  # 接收书籍列表
        db: AsyncSession = Depends(get_database)
):
    # 1. 批量转换为ORM模型实例
    # // Stream.map().collect()（批量转换+收集）
    #         List<Book> ormBookList = bookList.stream()
    #                 // map()：对应 Python 中 Book 实例化的转换逻辑
    #                 .map(item -> new Book(
    #                         item.getBookname(),
    #                         item.getAuthor(),
    #                         item.getPrice(),
    #                         item.getPublisher()
    #                 ))
    #                 // collect()：对应 Python 外层 []，收集为 List
    #                 .collect(Collectors.toList());
    orm_book_list = [
        Book(
            bookname=item.bookname,
            author=item.author,
            price=item.price,
            publisher=item.publisher
        )
        for item in book_list
    ]
    # 2. 批量添加到会话（效率高于循环add）
    db.add_all(orm_book_list)
    # 3. 提交事务
    await db.commit()
    # 4. 批量刷新实例
    for book in orm_book_list:
        await db.refresh(book)

    return Results[list[Book]](
        code=200,
        message=f"批量新增成功，共新增 {len(orm_book_list)} 本图书",
        data=orm_book_list
    )


# -------------------------- 二、修改操作（U：Update） --------------------------
@app.put("/book/update/{book_id}", summary="1. 单条书籍更新（先查询后更新，安全推荐）", response_model=Results[Book])
async def update_single_book(
        book_id: int = Path(..., gt=0, description="书籍主键ID"),  # 必填路径参数
        book_info: BookUpdate = ...,  # 将其显式设为必填（使用 ...）
        db: AsyncSession = Depends(get_database)  # 依赖注入通常放在最后
):
    # 1. 先查询书籍是否存在
    book = await db.get(Book, book_id)
    if not book:
        return Results[Book](
            code=404,
            message=f"书籍不存在（ID：{book_id}）",
            data=None
        )
    # 2. 部分更新（仅更新非None的字段）
    update_data = book_info.dict(exclude_unset=True)  # 排除未传入的字段（值为None的字段不更新）
    for key, value in update_data.items():
        setattr(book, key, value)
    # 3. 提交事务（自动触发update_time更新）
    await db.commit()
    # 4. 刷新实例
    await db.refresh(book)

    return Results[Book](
        code=200,
        message="书籍更新成功",
        data=book
    )


@app.put("/book/update/batch", summary="2. 批量书籍更新（按条件更新，高效）", response_model=Results[int])
async def update_batch_books(
        publisher: str = Query(..., description="要更新的书籍出版社"),
        new_price: float = Query(..., gt=0, description="新价格"),
        db: AsyncSession = Depends(get_database)
):
    # 1. 直接执行批量更新语句（无需先查询，效率更高）
    update_stmt = (
        Book.__table__.update()
        .where(Book.publisher == publisher)
        .values(price=new_price)  # 可同时更新多个字段，如 values(price=new_price, author="未知")
    )
    # 2. 执行更新
    result = await db.execute(update_stmt)
    # 3. 提交事务
    await db.commit()
    # 获取受影响的行数
    affected_rows = result.rowcount

    return Results[int](
        code=200,
        message=f"批量更新成功，共更新 {affected_rows} 本图书（出版社：{publisher}）",
        data=affected_rows
    )


# -------------------------- 三、删除操作（D：Delete） --------------------------
@app.delete("/book/delete/{book_id}", summary="1. 单条书籍删除（先查询后删除，安全推荐）", response_model=Results[None])
async def delete_single_book(
        book_id: int = Path(..., gt=0, description="书籍主键ID"),
        db: AsyncSession = Depends(get_database)
):
    # 1. 先查询书籍是否存在
    book = await db.get(Book, book_id)
    if not book:
        return Results[None](
            code=404,
            message=f"书籍不存在（ID：{book_id}）",
            data=None
        )
    # 2. 删除实例
    await db.delete(book)
    # 3. 提交事务
    await db.commit()

    return Results[None](
        code=200,
        message="书籍删除成功",
        data=None
    )


@app.delete("/book/delete/batch", summary="2. 批量书籍删除（按条件删除，高效）", response_model=Results[int])
async def delete_batch_books(
        min_price: float = Query(..., ge=0, description="删除价格低于该值的书籍"),
        db: AsyncSession = Depends(get_database)
):
    # 1. 方式1：先查询再批量删除（可验证数据，安全）
    # result = await db.execute(select(Book).where(Book.price < min_price))
    # books_to_delete = result.scalars().all()
    # for book in books_to_delete:
    #     await db.delete(book)
    # affected_rows = len(books_to_delete)

    # 方式2：直接执行批量删除语句（效率更高，推荐批量大量删除）
    delete_stmt = Book.__table__.delete().where(Book.price < min_price)
    result = await db.execute(delete_stmt)
    affected_rows = result.rowcount  # 获取受影响的行数

    # 提交事务
    await db.commit()

    return Results[int](
        code=200,
        message=f"批量删除成功，共删除 {affected_rows} 本图书（价格 < {min_price}）",
        data=affected_rows
    )
# endregion