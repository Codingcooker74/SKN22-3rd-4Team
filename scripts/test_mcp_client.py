"""
MCP 클라이언트 테스트 스크립트
Claude Desktop 없이 Python 코드에서 직접 MCP 서버를 실행하고 툴을 호출합니다.
"""

import asyncio
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.getcwd())

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    print("🔌 Finnhub MCP 서버에 연결 중...")
    
    # 1. MCP 서버 실행 파라미터 설정
    server_params = StdioServerParameters(
        command="python", # 현재 환경의 python 사용
        args=["src/tools/finnhub_server.py"],
        env=os.environ.copy() # 현재 환경 변수(.env 포함) 전달
    )

    # 2. 서버 연결 및 세션 시작
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 초기화
            await session.initialize()
            
            # 3. 사용 가능한 툴 목록 조회
            tools = await session.list_tools()
            print(f"\n🛠️  발견된 툴 ({len(tools.tools)}개):")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description[:50]}...")
            
            # 4. 툴 호출 테스트 (애플 주가 조회)
            print("\n📈 'get_stock_quote' 툴 호출 (Symbol: AAPL)...")
            result = await session.call_tool("get_stock_quote", arguments={"symbol": "AAPL"})
            
            # 5. 결과 출력
            print("\n📊 결과 확인:")
            if result.content:
                print(result.content[0].text)
            else:
                print("결과 없음")

if __name__ == "__main__":
    asyncio.run(main())
