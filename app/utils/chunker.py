from langchain.text_splitter import RecursiveCharacterTextSplitter

async def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=0
    )
    return splitter.split_text(text)
