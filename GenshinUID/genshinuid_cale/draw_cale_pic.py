from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.image.convert import convert_img

from ..utils.api.mys.models import Act, FixedAct
from ..utils.mys_api import mys_api, get_base_data
from ..utils.resource.download_url import download
from ..genshinuid_xkdata.draw_teyvat_img import gen_char
from ..utils.fonts.genshin_fonts import gs_font_26, gs_font_30, gs_font_38
from ..utils.resource.RESOURCE_PATH import CHAR_PATH, TEMP_PATH, WEAPON_PATH
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    get_avatar,
    get_v4_title,
)

GREY = (189, 189, 189)
TEXT_PATH = Path(__file__).parent / 'texture2d'
yes = Image.open(TEXT_PATH / 'yes.png')
no = Image.open(TEXT_PATH / 'no.png')


def convert_timestamp_to_string(timestamp):
    days = timestamp // (24 * 3600)
    hours = (timestamp % (24 * 3600)) // 3600
    minutes = (timestamp % 3600) // 60

    result = f"{days}天{hours}时{minutes}分"
    return result


async def draw_act(act: Union[Act, FixedAct]):
    act_bg = Image.open(TEXT_PATH / 'act_bg.png')

    fg = yes if act['is_finished'] else no
    t = '已完成' if act['is_finished'] else '未完成'

    act_bg.paste(fg, (0, 0), fg)
    act_draw = ImageDraw.Draw(act_bg)

    act_name = act['name']
    limit_time = '剩余时间：' + convert_timestamp_to_string(
        act['countdown_seconds']
    )

    act_draw.text((94, 60), act_name, 'white', gs_font_38, 'lm')
    act_draw.text((130, 102), limit_time, GREY, gs_font_26, 'lm')

    act_draw.text((840, 81), t, 'white', gs_font_30, 'mm')

    for j, reward in enumerate(act['reward_list'][:2]):
        icon_bg = Image.open(TEXT_PATH / 'icon_bg.png')
        icon_fg = Image.open(TEXT_PATH / 'icon_fg.png')
        ipath = TEMP_PATH / f'{reward["name"]}.png'
        num = reward['num']

        if not ipath.exists():
            await download(reward['icon'], 16, f'{reward["name"]}.png')

        icon = Image.open(ipath)
        icon = icon.resize((100, 100))

        icon_bg.paste(icon, (0, 0), icon)
        icon_bg.paste(icon_fg, (0, 0), icon_fg)
        icon_draw = ImageDraw.Draw(icon_bg)

        icon_draw.text((50, 81), str(num), 'white', gs_font_26, 'mm')

        act_bg.paste(icon_bg, (539 + j * 105, 31), icon_bg)

    return act_bg


async def draw_cale_img(ev: Event, uid: str):
    data = await mys_api.get_calendar_data(uid)
    if isinstance(data, int):
        return get_error(data)

    raw_data = await get_base_data(uid)
    if isinstance(raw_data, (str, bytes)):
        return raw_data
    elif isinstance(raw_data, (bytearray, memoryview)):
        return bytes(raw_data)

    char_pic = await get_avatar(ev, 377, False)
    title_img = get_v4_title(char_pic, uid, raw_data)

    title_img = title_img.resize((1058, 441))

    w, h = 1000, title_img.size[1] + 385

    if data['avatar_card_pool_list']:
        h += 270
    if data['weapon_card_pool_list']:
        h += 270

    h += len(data['act_list']) * 160
    h += len(data['fixed_act_list']) * 160

    img = get_v4_bg(w, h)

    img.paste(title_img, (-30, 34), title_img)

    p = title_img.size[1] + 60
    bar1 = Image.open(TEXT_PATH / 'bar1.png')
    img.paste(bar1, (0, p), bar1)

    p += 60
    if data['avatar_card_pool_list']:
        pool_bg = Image.open(TEXT_PATH / 'pool_bg.png')
        pool_draw = ImageDraw.Draw(pool_bg)

        fd = data['avatar_card_pool_list'][0]
        pool_draw.text((159, 61), fd['pool_name'], 'white', gs_font_38, 'lm')
        pool_draw.text(
            (110, 61), fd['version_name'], 'white', gs_font_30, 'mm'
        )
        limit_time = '剩余时间：' + convert_timestamp_to_string(
            fd['countdown_seconds']
        )
        pool_draw.text((110, 106), limit_time, GREY, gs_font_26, 'lm')

        for index, ap in enumerate(data['avatar_card_pool_list']):
            avatars = ap['avatars']

            for aindex, avatar in enumerate(avatars):
                cpath = CHAR_PATH / f"{avatar['id']}.png"
                if not cpath.exists():
                    await download(avatar['icon'], 1, f"{avatar['id']}.png")
                char = Image.open(cpath)
                char_bg = gen_char(char, avatar['rarity'])
                char_bg = char_bg.resize((105, 105))

                pool_bg.paste(
                    char_bg,
                    (64 + aindex * 105 + index * 444, 136),
                    char_bg,
                )
        img.paste(pool_bg, (0, p), pool_bg)
        p += 270

    if data['weapon_card_pool_list']:
        pool_bg = Image.open(TEXT_PATH / 'pool_bg.png')
        pool_draw = ImageDraw.Draw(pool_bg)

        fd = data['weapon_card_pool_list'][0]
        pool_draw.text((159, 61), fd['pool_name'], 'white', gs_font_38, 'lm')
        pool_draw.text(
            (110, 61), fd['version_name'], 'white', gs_font_30, 'mm'
        )
        limit_time = '剩余时间：' + convert_timestamp_to_string(
            fd['countdown_seconds']
        )
        pool_draw.text((110, 106), limit_time, GREY, gs_font_26, 'lm')

        for index, wp in enumerate(data['weapon_card_pool_list']):
            weapon = wp['weapon']

            for windex, weapon in enumerate(weapon):
                cpath = WEAPON_PATH / f"{weapon['name']}.png"
                if not cpath.exists():
                    await download(weapon['icon'], 5, f"{weapon['name']}.png")
                char = Image.open(cpath)
                char_bg = gen_char(char, weapon['rarity'])
                char_bg = char_bg.resize((105, 105))

                pool_bg.paste(
                    char_bg,
                    (64 + windex * 105 + index * 444, 136),
                    char_bg,
                )
        img.paste(pool_bg, (0, p), pool_bg)
        p += 270

    p += 30
    bar2 = Image.open(TEXT_PATH / 'bar2.png')
    img.paste(bar2, (0, p), bar2)
    p += 60

    for act in data['act_list']:
        act_bg = await draw_act(act)
        img.paste(act_bg, (0, p), act_bg)
        p += 160

    p += 30
    bar3 = Image.open(TEXT_PATH / 'bar3.png')
    img.paste(bar3, (0, p), bar3)
    p += 60

    for fixed_act in data['fixed_act_list']:
        fixed_act_bg = await draw_act(fixed_act)
        img.paste(fixed_act_bg, (0, p), fixed_act_bg)
        p += 160

    img = add_footer(img, 1000)
    return await convert_img(img)
