import sys
sys.path.append('/home/niuhaojia/lit-llama/generate')
from tqdm import tqdm
import re
import ast
import os
import json
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.huggingface import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from lora import generate_response
from transformers import set_seed
set_seed(101)
sys.setrecursionlimit(10000)  # 设置一个更高的递归深度限制

# 定义文件夹路径
json_folder = "/home/niuhaojia/file/22/aunt/1_2"
txt_folder = "/home/niuhaojia/file/22/aunt/1"
txt_folder_2 = "/home/niuhaojia/file/22/aunt/1_1"
if not os.path.exists("/home/niuhaojia/file/22/aunt/faiss"):
    os.makedirs("/home/niuhaojia/file/22/aunt/faiss")
faiss_folder = "/home/niuhaojia/file/22/aunt/faiss"
if not os.path.exists("/home/niuhaojia/file/22/aunt/1_3"):
    os.makedirs("/home/niuhaojia/file/22/aunt/1_3")
output_folder = "/home/niuhaojia/file/22/aunt/1_3"

# 获取json文件列表
json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
json_files.sort() 

# 创建一个嵌入对象并设置模型的名称
embeddings = HuggingFaceInstructEmbeddings(
    model_name="/home/css/models/bge-large-en-v1.5", model_kwargs={'device': 'cuda'},
    query_instruction="Represent this sentence for searching relevant passages:"
)

# 遍历处理每个json文件
for json_file in tqdm(json_files):
    # 检查是否存在_3.json文件
    output_file = json_file.replace('_2.json', '_3.json')
    if os.path.exists(os.path.join(output_folder, output_file)):
        continue
    # 加载并解析JSON文件
    with open(os.path.join(json_folder, json_file), 'r') as file:
        data = json.load(file)

    # try:    
    # 使用你选择的文件路径和loader加载文档
    txt_file = json_file.replace('_2.json', '.txt')  # 根据你的规则来匹配对应的txt文件
    filepath = os.path.join(txt_folder, txt_file)
    loader = TextLoader(filepath)
    docs = loader.load()

    # 创建一个文本分割器并分割文档
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    docs = text_splitter.split_documents(docs)

    # 对每个json文件，都生成一份新的向量库
    vectorstore_path = os.path.join(faiss_folder, json_file.replace('.json', '.faiss'))
    if not os.path.exists(vectorstore_path):
        vector_store = FAISS.from_documents(docs, embeddings)
        vector_store.save_local(vectorstore_path)
    else:
        vector_store = FAISS.load_local(vectorstore_path, embeddings=embeddings)
    
    print(output_file)
    
    txt_file_2 = json_file.replace('_2.json', '_1.txt')  
    filepath_2 = os.path.join(txt_folder_2, txt_file_2)
    # 读取filepath_2的内容到一个列表
    with open(filepath_2, 'r') as f:
        lines = f.readlines()
    # 跳过第一行
    lines = lines[1:]

    # try:
    # 遍历处理数据的每一项
    for i, (d, line) in enumerate(zip(data, lines)):          
        # # 从data中获取人名和关系
        # person1, gender1, person2, gender2, relationship = d
        # if person2 == 'unknown':
        #     person2 = 'an unknown person'
        # # 使用data中的信息构建查询字符串
        # query = f'''
        # In this sentence, We can infer the following quintuple relationship:'["{person1}","{gender1}","{person2}","{gender2}","{relationship}"]'. This means that {person1} is a {gender1}, {person2} is a {gender2}, and the relationship between {person1} and {person2} is {relationship}. May I ask, in this sentence, the two people who conform to the {relationship} relationship, are there any extraction errors.If there is a mistake, please find the two people who match the {relationship} relationship from this sentence. Always follow this quintuple format, please give your answer: '["Person's Name","gender"," Person's Name ","gender", "{relationship}"]'. If there is an unknown element, replace it with "unknown".
        # '''
        # # 清除行两端的空格并进行相似性搜索
        # docs = vector_store.similarity_search(line.strip())  

        query2 = f'Please analyze the following sentence and extract the earliest explicit time-related information. If multiple timestamps are present, choose the earliest one. If only the year is mentioned, output it in the format \'YYYY-MM\', with \'MM\' representing the missing month. If only the month is mentioned, output it in the format \'YYYY-MM\', with \'YYYY\' representing the missing year. If both the year and the month are mentioned, output the time information in the format \'YYYY-MM\'. If there is no explicit time-related information that includes both the year and the month, output \'YYYY-MM\' to indicate that both the year and the month are unknown.Always remember to answer in the format \'YYYY-MM\'.\nSentence: "{line.strip()}".'
        timestamp = generate_response(prompt=query2)
        print(timestamp)
        # 检查timestamp格式并提取YYYY-MM部分
        timestamp_pattern = re.compile(r'^(\d{4}-(0?[1-9]|1[0-2]|MM))(-\d{1,2}|-\d{1,2})?$')
        match = timestamp_pattern.match(timestamp)
        if match:
            # 提取YYYY-MM部分
            year_month = match.group(1)
            data[i].append(year_month)
            print("提取到时间"+ str(data[i]))
        else:
            data[i].append('YYYY-MM')
            print("没有提取到时间"+str(data[i]))

        # # Get and print the answer generated by generate_response
        # context = [doc.page_content for doc in docs]
        # my_input = "\n".join(context)
        # prompt=f"Given:\n{my_input}\nPlease answer: {query}"
        # try: 
        #     response = generate_response(prompt=prompt)
        # except Exception as e:
        #     print(f"{e}\nSkipping file {json_file} due to CUDA error. {i}")
        #     continue
        # 检查response是否为空或者不是有效的JSON格式
        # try:
        #     response_list = json.loads(response)
        # except Exception:
        #     continue
        
        # # 检查response_list是否是一个5元组
        # if len(response_list) != 5:
        #     continue
        # # 检查response_list中的关系是否与data[i]中的关系相同
        # if response_list[4] != d[4]:
        #     continue
        # # 检查response_list中的1和3位置是否是性别
        # if response_list[1] not in ['male', 'female', 'unknown'] or response_list[3] not in ['male', 'female', 'unknown']:
        #     continue

        # data[i] = response_list
        
    # except Exception as e:
    #     print(f"Skipping file {json_file} due to CUDA error.")    
        

    # 将结果保存到新的文件
    output_file = json_file.replace('_2.json', '_3.json')
    with open(os.path.join(output_folder, output_file), 'w') as file:
        json.dump(data, file, indent=4)
        print("by777")
    
    break