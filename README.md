# Deploy a Python (Flask) web app to Azure App Service - Sample Application
https://medium.com/@gaurav.jaik86/building-an-ai-powered-chat-with-pdf-app-with-streamlit-langchain-faiss-and-llama2-affadea65737 
1. Download the Llama2 model from - https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
2. Create 3 .py files as:
  a. app.py -> To create app interface
  b. loadllm.py -> To load the Llama2 model locally
  c. fileingestor.py -> To upload PDF file and create chain for question answering
3. Run command "streamlit run app.py" -> This will run the app on http://localhost:8501
4. I have used UPI booklet - https://www.npci.org.in/PDF/npci/upi/Product-Booklet.pdf
*https://visualstudio.microsoft.com/visual-cpp-build-tools/ 
python.exe -m pip install --upgrade pip
pip install --upgrade pip setuptools wheel
https://github.com/ggerganov/llama.cpp#openblas
https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#openblas
is required by "pip install llama-cpp-python"
$env:CMAKE_ARGS = "-DLLAMA_OPENBLAS=on"
set FORCE_CMAKE=1
set CMAKE_ARGS="-DLLAMA_AVX2=OFF"
explained https://stackoverflow.com/questions/77267346/error-while-installing-python-package-llama-cpp-python 

jamesqh commented on May 27 • 
Figured this out myself. The error message was kinda backwards: the problem isn't that the dll isn't a valid Win32 application, but that it is and it shouldn't be!

I was using "Developer Command Prompt for VS 2022", and I guess that compiles it to 32 bit. The solution is to use x64 Native Tools Command Prompt for VS 2022 instead. pip install llama-cpp-python in that environment installs a dll that fails to load models because of "Windows Error 0xc000001d", which in my case seems to mean that the binary is trying to use AVX2 without success. set FORCE_CMAKE=1 and set CMAKE_ARGS="-DLLAMA_AVX2=OFF" followed by the pip install gives me a llama-cpp-python that... well, fails to load a model due to "Windows Error 0xe06d7363", but that seems like a separate issue and at least it's actually importing the module now.

(Windows Error 0xe06d7363 was due to all the models I was trying to use being wrong versions. My kingdom for a set of standardised tiny test models)

python -m venv myvirtenv

This is the sample Flask application for the Azure Quickstart [Deploy a Python (Django or Flask) web app to Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/quickstart-python). For instructions on how to create the Azure resources and deploy the application to Azure, refer to the Quickstart article.

Sample applications are available for the other frameworks here:

* Django [https://github.com/Azure-Samples/msdocs-python-django-webapp-quickstart](https://github.com/Azure-Samples/msdocs-python-django-webapp-quickstart)
* FastAPI [https://github.com/Azure-Samples/msdocs-python-fastapi-webapp-quickstart](https://github.com/Azure-Samples/msdocs-python-fastapi-webapp-quickstart)

If you need an Azure account, you can [create one for free](https://azure.microsoft.com/en-us/free/).
