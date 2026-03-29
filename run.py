import uvicorn
import argparse
import sys
import os

# Ensure the root directory is in sys.path so modules can find each other
sys.path.append(os.path.dirname(__file__))

def main():
    parser = argparse.ArgumentParser(description="EPINEON AI - Elite Management Console")
    parser.add_argument("--port", type=int, default=8000, help="API Port (Default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="API Host (Default: 127.0.0.1)")
    parser.add_argument("--collect-only", action="store_true", help="Run data collection and exit")
    
    args = parser.parse_args()

    if args.collect_only:
        import asyncio
        from engine.collector import fetch_and_store_data
        print("[PIPELINE] Starting manual data collection...")
        asyncio.run(fetch_and_store_data())
        print("[SUCCESS] Collection complete.")
        return

    print("[BOOT] Initializing EPINEON AI Control Center...")
    print(f"[WEB] Access Dashboard at http://{args.host}:{args.port}")
    
    # Run uvicorn on api.main:app
    uvicorn.run("api.main:app", host=args.host, port=args.port, reload=True)

if __name__ == "__main__":
    main()
