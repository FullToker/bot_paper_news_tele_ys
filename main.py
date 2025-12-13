import arxiv
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler


# 1. 定义获取论文的函数
def get_arxiv_papers(category, max_results=3):
    client = arxiv.Client()
    # 构造搜索查询，例如 "cat:cs.CV"
    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,  # 按提交时间排序
    )

    papers = []
    for result in client.results():
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

    papers = get_arxiv_papers("cs.CV")

    for paper in papers:
        # 发送每篇论文的信息
        msg = f"📄 **{paper['title']}**\n\n📅 日期: {paper['date']}\n\n📝 **摘要:**\n{paper['summary'][:300]}...\n\n🔗 [PDF链接]({paper['url']})"
        await update.message.reply_text(msg, parse_mode="Markdown")


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

    application.run_polling()
