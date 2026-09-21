## (1) What I used an AI assistant for and what I did myself
I used an AI assistant to help with understanding the llama functions and how to implement them. I also used it to help create the preprocessing functions for the corpus as I had issues with the file encoding.
I also needed help to create a script for the corpus manifest details, as I was unfamiliar with how to obtain sha256 hash. Furthermore, I used it as a debugging tool to help with coding errors. 
All manual observations and analysis were my own. 

## (2) One AI-produced output that was wrong/unsuitable, or one thing I independently verified
One unsuitable approach that was suggested was using SimpleDirectoryReader to load all of the corpus files. The PDFs were loaded as raw PDF data containing text such as %PDF, endobj, and xref, while the HTML files included HTML tags and a large amount of navigation text. I independently verified the PDF extraction by testing pypdf directly on one of the files.

## (3) How I detected the problem or verified the result
I detected the problem by printing previews from the loaded documents before running retrieval. The previews showed that the PDFs did not contain readable policy text and that the HTML files contained tags and irrelevant website navigation. I then used pypdf.PdfReader and extract_text() on an individual PDF and confirmed that it returned readable text. I also checked the cleaned HTML previews and verified that all six corpus files were still included.

## (4) What I changed and why it works now
I changed the corpus loader to use pypdf for the PDF files and BeautifulSoup for the HTML files. For the HTML files, I removed navigation, header, footer, script, and style elements before extracting the text. I also tested the PDF layout extraction mode. The final loader now produces readable text for all six files, which allows the LlamaIndex chunking and retrieval techniques to operate on document content instead of raw PDF data or website navigation text.However, there were still some parsing issues which are documented as a limitation. 