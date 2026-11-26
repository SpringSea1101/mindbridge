from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.bootstrap import create_schema, seed_data
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.tool_queue import get_tool_queue_worker


def create_app() -> FastAPI:
    app = FastAPI(title="MindBridge Python", version="0.1.0")
    # 创建Web应用程序实例，并设置标题和版本号。

    @app.middleware("http")
    # middleware 装饰器用于注册一个中间件函数，该函数将在每个请求处理之前和之后执行。
    # async：异步操作
    async def no_cache_frontend_assets(request, call_next):
        # 让这个request继续往下走，让FastAPI正常处理它，然后把处理结果拿回来。
        # call_next(request) 是一个异步函数，
        # 它会将请求传递给下一个中间件或最终的请求处理器，并返回响应对象。
        response = await call_next(request)
        path = request.url.path
        if path == "/" or path.endswith((".html", ".js", ".css")):
            response.headers["Cache-Control"] = "no-store"  # 让浏览器不要缓存这个文件
        return response

    @app.on_event("startup")
    def startup() -> None:
        create_schema()  # 创建数据库模式（schema），确保数据库结构已经建立。
        db = SessionLocal()
        try:
            seed_data(db)   # 向数据库中插入初始数据，确保应用程序在启动时有必要的数据可用。
        finally:    # 无论是否发生异常，都会执行 finally 块中的代码，确保数据库会话被关闭。
            db.close()
        worker = get_tool_queue_worker(get_settings())
        worker.start()
        # app.state 是 FastAPI 提供的一个特殊对象，用于在应用程序的生命周期内存储状态信息。
        app.state.tool_queue_worker = worker

    @app.on_event("shutdown")
    def shutdown() -> None:
        # 下面这段代码可以粗略理解为 worker = get_tool_queue_worker(get_settings())
        # 如果tool_queue_worker存在，就调用它的stop方法，停止工具队列工作线程。
        # 如果tool_queue_worker不存在，就不做任何操作。
        worker = getattr(app.state, "tool_queue_worker", None)
        if worker is not None:
            worker.stop()

    # 将路由器对象（API接口）注册到应用程序中，使得应用程序能够处理定义在路由器中的所有API端点。
    app.include_router(router)
    static_dir = Path(__file__).resolve().parent / "static"
    # 将静态文件目录设置为当前文件所在目录的 "static" 子目录。
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app


app = create_app()
