from transformers import DistilBertModel, DistilBertTokenizerFast
from transformers import pipeline
 
# 加载预训练的DistilBERT模型和分词器
tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
model = DistilBertModel.from_pretrained('distilbert-base-uncased')
 
# 使用pipeline函数创建情感分析器
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)
 
# 进行情感分析
text = "I love this movie!"
result = classifier(text)[0]
print(result)