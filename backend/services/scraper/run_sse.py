import sys
import linkedin_mcp_server.cli_main

# Fake args so argparse doesn't fail
sys.argv = ["linkedin_mcp_server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080"]

original_create = linkedin_mcp_server.cli_main.create_mcp_server

def hooked_create(*args, **kwargs):
    mcp = original_create(*args, **kwargs)
    original_run = mcp.run
    def hooked_run(*r_args, **r_kwargs):
        print("Intercepted mcp.run, forcing SSE transport!")
        return original_run(transport="sse", host="0.0.0.0", port=8080)
    mcp.run = hooked_run
    return mcp

linkedin_mcp_server.cli_main.create_mcp_server = hooked_create

if __name__ == "__main__":
    linkedin_mcp_server.cli_main.main()
