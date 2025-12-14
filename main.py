import arxiv
import os
from html import escape
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.constants import ParseMode


# 1. 定义获取论文的函数
def get_arxiv_papers(query, max_results=5, treat_as_category=False):
    """Search arXiv by query or category."""
    client = arxiv.Client()

    # 将类别转换为 cat: 前缀，否则默认按关键词搜索全文
    if treat_as_category and not query.startswith("cat:"):
        search_query = f"cat:{query}"
    else:
        # 如果没有使用字段限定符，默认走全文搜索
        search_query = query if ":" in query else f"all:{query}"

    # 构造搜索查询
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,  # 按提交时间排序
    )

    papers = []
    for result in client.results(search):
        papers.append(
            {
                "title": result.title,
                "summary": result.summary,  # 摘要
                "url": result.pdf_url,
                "date": result.published.strftime("%Y-%m-%d"),
            }
        )
    return papers


# 2. 定义命令处理函数 (例如处理 /cv)
async def cv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("正在搜索最新的计算机视觉(CV)论文...")

    papers = get_arxiv_papers("cs.CV", treat_as_category=True)

    for paper in papers:
        # 发送每篇论文的信息
        msg = f"📄 **{paper['title']}**\n\n📅 日期: {paper['date']}\n\n📝 **摘要:**\n{paper['summary'][:300]}...\n\n🔗 [PDF链接]({paper['url']})"
        await update.message.reply_text(msg, parse_mode="Markdown")

# 2.1 自定义搜索
async def search_paper_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. 获取用户输入的参数
    # 如果用户输入: /paper 3dgs
    # context.args 就是 ['3dgs']
    # 如果用户输入: /paper 3d reconstruction
    # context.args 就是 ['3d', 'reconstruction']
    
    if not context.args:
        await update.message.reply_text("❗️ 请在命令后输入关键词，例如: `/subscribe 3dgs`", parse_mode="Markdown")
        return

    # 将参数拼接成一个字符串
    keyword = " ".join(context.args)
    status_msg = f"🔍 正在搜索关键词: **{keyword}** ..."

    await update.message.reply_text(status_msg, parse_mode="Markdown")

    # 2. 调用之前的搜索函数，传入动态 keyword
    # 注意：你需要确保你的 get_arxiv_papers 函数能接收 query 参数
    papers = get_arxiv_papers(keyword, max_results=10)

    if not papers:
        await update.message.reply_text("❌ 未找到相关论文，请尝试更换关键词。")
        return

    for paper in papers:
        # 发送每篇论文的信息
        title = escape(paper["title"])
        summary = escape(paper["summary"][:500])
        url = escape(paper["url"])

        msg = (
          f"📄 <b>{title}</b>\n\n"
          f"📅 日期: {paper['date']}\n\n"
          f"📝 <b>摘要:</b>\n{summary}...\n\n"
          f"🔗 <a href=\"{url}\">PDF链接</a>"
        )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)



# 3. show all commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. 静态命令
    text = (
        "<b>🤖 Bot 命令列表:</b>\n\n"
        "<b>基础命令:</b>\n"
        "/start - 开始使用\n"
        "/aindex - arxiv 索引\n"
        "/help - 显示此帮助\n\n"
        "<b>论文搜索:</b>\n"
        "/subscribe &lt;关键词&gt; - 搜索论文\n" 
        "例如: <code>/subscribe 3dgs</code>\n\n"
        "<b>高级搜索:</b>\n"
        "指定分类: <code>/subscribe 3dgs AND cat:cs.CV</code>"
        )

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
# 定义常用分类字典
CATEGORIES = {
    "cv": "cs.CV (计算机视觉)",
    "nlp": "cs.CL (自然语言处理)",
    "ml": "cs.LG (机器学习)",
    "ai": "cs.AI (人工智能)",
    "robot": "cs.RO (机器人)",
}

async def list_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📚 **支持的 arXiv 分类速查:**\n\n"
    for key, desc in CATEGORIES.items():
        msg += f"• `{key}` -> {desc}\n"
    
    msg += "\n💡 使用方法: `/paper cat:cs.CV`"
    await update.message.reply_text(msg, parse_mode='Markdown')

# 3. 主程序
if __name__ == "__main__":
    # 加载 .env 文件
    load_dotenv()

    # 获取变量
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    application = ApplicationBuilder().token(TOKEN).build()

    # 注册命令
    cv_handler = CommandHandler("cv_huge", cv_command)
    application.add_handler(cv_handler)

    topic_handler = CommandHandler("subscribe", search_paper_command)
    application.add_handler(topic_handler)

    arxiv_index_handler = CommandHandler("aindex", list_categories)
    application.add_handler(arxiv_index_handler)

    help_handler = CommandHandler("help", help_command)
    application.add_handler(help_handler)

    application.run_polling()
