import uvicorn
import argparse

if __name__ == "__main__":
    uvicorn_parser = argparse.ArgumentParser(description='Run the ScholarQA API with uvicorn args')
    uvicorn_parser.add_argument('--target', type=str, default="scholarqa.app:create_app",
                                help='The target ASGI app to run. Default is scholarqa.app:create_app')
    uvicorn_parser.add_argument('--reload', action='store_true', help='Enable auto-reload', default=False)
    uvicorn_parser.add_argument('--log-level', type=str, default="warning", help='Api access log level')
    uvicorn_parser.add_argument('--host', type=str, default="0.0.0.0", help='Host to bind to')
    uvicorn_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    uvicorn_parser.add_argument('--workers', type=int, default=1, help='Number of worker processes')
    uvicorn_parser.add_argument('--timeout-keep-alive', type=int, default=0, help='Timeout for keep-alive connections')

    uvicorn_args = uvicorn_parser.parse_args()
    uvicorn.run(uvicorn_args.target, reload=uvicorn_args.reload, log_level=uvicorn_args.log_level,
                host=uvicorn_args.host, port=uvicorn_args.port,
                workers=uvicorn_args.workers, timeout_keep_alive=uvicorn_args.timeout_keep_alive)
