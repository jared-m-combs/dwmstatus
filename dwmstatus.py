#!/usr/bin/env python3
import asyncio
import re
import logging as log
from datetime import datetime
from typing import Optional, AsyncGenerator


Update = dict[str,Optional[str]]
UpdateGenerator = AsyncGenerator[Update,None]


async def exec(cmd: str, *args: str) -> int:
    proc = await asyncio.create_subprocess_exec(cmd, *args)
    return await proc.wait()

async def exec_read(cmd: str, *args: str) -> str:
    proc = await asyncio.create_subprocess_exec(cmd, *args, stdout=asyncio.subprocess.PIPE)
    assert proc.stdout is not None
    output = await proc.stdout.read()
    return output.decode().strip()

async def exec_readlines(cmd: str, *args: str) -> AsyncGenerator[str,None]:
    proc = await asyncio.create_subprocess_exec(cmd, *args, stdout=asyncio.subprocess.PIPE)
    assert proc.stdout is not None
    while line := await proc.stdout.readline():
        yield line.decode().strip()


async def playerctl() -> UpdateGenerator:
    async def get_players():
        output = await exec_read('playerctl', '-l')
        return output.split('\n') if output else []

    async def get_status(player: str) -> str:
        status = await exec_read('playerctl', '-p', player, 'status')
        return status.lower()

    async def get_metadata(player: str) -> dict[str,str]:
        output = await exec_read('playerctl', '-p', player, 'metadata')
        rows = re.findall(r'^[^:]+:([^\s]+)\s+(.*?)$', output, flags=re.MULTILINE)
        return dict(rows)

    async def get_currently_playing() -> Optional[dict[str,str]]:
        for player in await get_players():
            status = await get_status(player)
            if status == 'playing':
                return await get_metadata(player)

    async def create_update() -> Update:
        if metadata := await get_currently_playing():
            title = ' - '.join(metadata[k] for k in ['title', 'artist'] if k in metadata)
            return Update(media=title)
        else:
            return Update(media=None)

    yield await create_update()

    async for dbusline in exec_readlines('dbus-monitor', '--profile', "path='/org/mpris/MediaPlayer2'"):
        if m := re.search(r'[^\s]+$', dbusline):
            if m.group(0) in ['PropertiesChanged', 'Seeked']:
                yield await create_update()


async def pactl() -> UpdateGenerator:
    default_sink = await exec_read('pactl', 'get-default-sink')

    async def get_volume() -> Optional[str]:
        output = await exec_read('pactl', 'get-sink-volume', default_sink)
        if m := re.search(r'\d+%', output):
            return m.group(0)

    async def create_update() -> Update:
        vol = await get_volume()
        return Update(vol=vol)

    yield await create_update()
      
    async for line in exec_readlines('pactl', 'subscribe'):
        if re.match(r"Event 'change' on sink #", line):
            yield await create_update()


async def vmstat() -> UpdateGenerator:
    lines = exec_readlines('vmstat', '-n', '5')

    await anext(lines) # throw away first header line
    headerline = await anext(lines)
    headers = re.findall(r'[a-z]+', headerline)

    async for dataline in lines:
        fields = [int(a) for a in re.findall(r'\d+', dataline)]
        datamap = {h: f for h, f in zip(headers, fields)}
        cpu_usage = 100 - datamap['id'] 
        mem_avail = (datamap['free'] + datamap['buff'] + datamap['cache']) / 1024 / 1024
        yield Update(cpu=f'{cpu_usage}%', mem=f'{mem_avail:.2f}G')


async def date() -> UpdateGenerator:
    while True:
        now = datetime.now()
        yield Update(date=now.strftime('%a %m/%d %I:%M %p')) 
        await asyncio.sleep(65-now.second)


async def dwmstatus():
    slots = [
        ('media', ''),
        ('vol',   ''),
        ('cpu',   ''),
        ('mem',   ''),
        ('date',  '')
    ]

    generators = [
        playerctl,
        pactl,
        vmstat,
        date
    ]

    delim = ' '*2
    state = {}
    queue = asyncio.Queue()

    async def drain_to_queue(generator):
        while True:
            try:
                async for a in generator():
                    await queue.put(a)
            except:
                log.exception(None)
                await asyncio.sleep(5)

    for generator in generators:
        asyncio.create_task(drain_to_queue(generator))

    while update := await queue.get():
        if any(state.get(k) != v for k,v in update.items()):
            state.update(**update)
            statusline = delim.join(f'{icon} {state[k]}' for k, icon in slots if state.get(k))
            await exec('xsetroot', '-name', f' {statusline} ')


def main():
    asyncio.run(dwmstatus())


if __name__ == '__main__':
    main()
