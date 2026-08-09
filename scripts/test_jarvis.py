import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://127.0.0.1:8765') as ws:
        await ws.send(json.dumps({'tipo':'ping','origem':'health-check'}))
        try:
            msg=await asyncio.wait_for(ws.recv(),timeout=5)
            print('received:',msg)
        except Exception as e:
            print('error',e)
asyncio.run(test())