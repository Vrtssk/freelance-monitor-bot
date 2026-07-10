import re

from models.schemas import JobPosting

# Strong signals that a post is about building a native mobile / desktop
# application (iOS, Android, десктоп) rather than the user's web/parsing/
# script/bot topics.
_MOBILE_DESKTOP = re.compile(
    r"ios\b|android\b"
    r"|мобильн\w* приложен"
    r"|приложен\w* (под|для|под )?(ios|android)"
    r"|разработка (мобильного|мобильн\w*) приложен"
    r"|нативн\w* (приложен|приложение)"
    r"|xcode|swift\b|kotlin|flutter|swiftui|react native"
    r"|десктоп|desktop|windows[- ]приложен",
    re.I,
)

# In-scope signals — one of the user's actual topics (web frontend, website
# markup, parsing/scraping, scripts/automation, chatbots/telegram bots).
# Note: bare "верстка"/"вёрстка" is intentionally excluded — in app context it
# means "layout" (e.g. "верстка книжная"), which is NOT website markup.
_IN_SCOPE = re.compile(
    r"фронтенд|фронт-энд"
    r"|html|css|лендинг|figma|pixel.?perfect|кроссбраузерн"
    r"|адаптивн\w* верстк|верстк\w* (сайта|лендинг|страниц)"
    r"|спа\b|react\b|vue\b|next\.js|nuxt"
    r"|парсинг|парсер|scrap|скрап"
    r"|скрипт|автоматизаци"
    r"|бот\b|bot\b|chatbot|telegram|aiogram|telegraf|whatsapp|discord",
    re.I,
)


def is_off_topic(post: JobPosting) -> bool:
    """Return True if the posting is clearly OUTSIDE the user's topics.

    Used as a hard gate after the keyword pre-filter: a native mobile/desktop
    app build is rejected unless it also clearly needs one of the user's skills
    (e.g. a Telegram bot inside the app, parsing, web frontend work).
    """
    text = post.text_for_filter
    if not text or not _MOBILE_DESKTOP.search(text):
        return False
    # Mobile/desktop app post: relevant only if it also needs a user skill.
    return not _IN_SCOPE.search(text)
