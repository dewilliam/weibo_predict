#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import string
import numpy
import jieba
import jieba.analyse
from sklearn.neighbors import NearestNeighbors
def get_feature(line,this_feature):
	each_feature=[]
	time=line.split()[3].split(':')
	hour=int(time[0])
	mi=int(time[1])
	# 加入小时和分钟特征
	if hour<=4:
		each_feature.extend([1,0,0,0])
		pass
	elif hour<=9:
		each_feature.extend([0,1,0,0])
	elif hour<=19:
		each_feature.extend([0,0,1,0])
	elif hour<=21:
		each_feature.extend([0,0,0,1])
	else:
		each_feature.extend([0,0,0,0])
	if mi<=10:
		each_feature.extend([1,0])
		pass
	elif mi<=33 and mi>=27:
		each_feature.extend([0,1])
	else:
		each_feature.extend([0,0])
	# 处理文本之前统计ＵＲＬ
	http_num=line.count('http://')+line.count('https://')
	if http_num==0:
		each_feature.extend([0])
		pass
	else:
		each_feature.extend([1])
	#处理微博内容
	line=re.sub('http[s]*://(.*)/[a-zA-Z0-9]+','',line)
	start_pos=line.find('分享自')
	if start_pos==-1:
		start_pos=line.find('来自')
		if start_pos==-1:
			start_pos=line.find('via')
			pass
		pass
	# 如果有官微信息就清除
	if start_pos>0:
		end_pos=start_pos
		# while循序防止中间的分隔符导致清除不完整
		while end_pos-start_pos<3:
			# 三种情况，括号结尾，空格结尾，直到句子尾部
			end_pos=line.find(')',end_pos)
			if end_pos==-1:
				end_pos=line.find(' ',end_pos)
				if end_pos==-1:
					end_pos=len(line)
					pass
				pass
		line=line.replace(line[start_pos:end_pos],'')
		pass
	pass
	line=re.sub('@RAIN-JIHOON','',line)
	line=re.sub('@支付宝钱包','',line)
	line=string.join(line.split()[7:],'').strip()
	at_num=line.count('@')
	if at_num<=1:
		each_feature.extend([1,0,0])
		pass
	elif at_num<=3:
		each_feature.extend([0,1,0])
	elif at_num<=8:
		each_feature.extend([0,0,1])
	else:
		each_feature.extend([0,0,0])
	# 文本长度，因为是中文编码，所以要除以三才是正确的字个数
	str_len=len(line)/3
	if str_len<=13:
		each_feature.extend([1,0,0])
		pass
	elif str_len<=62:
		each_feature.extend([0,1,0])
	elif str_len<=108:
		each_feature.extend([0,0,1])
	else:
		each_feature.extend([0,0,0])
	topic_num=line.count('#')/2
	if topic_num<=3:
		each_feature.extend([1])
		pass
	else:
		each_feature.extend([0])
	title_num=line.count('【')
	if title_num<=1:
		each_feature.extend([1])
		pass
	else:
		each_feature.extend([0])
	this_feature.append(each_feature)
	return line,each_feature

def get_word_vector(data,this_feature):
	if len(data):
		for j in range(0,50):
			word=words[j].encode('utf-8')
			word_count=data.count(word)
			if word_count:
				this_feature.extend([1])
			else:
				this_feature.extend([0])
			pass
	else:
		for j in range(50):
			this_feature.extend([0])


avar=0
D=0.0
num=0
train_file_name='train_train_data'
test_file_name='train_test_data'
# 求评论数平均数和方差，去掉三个方差之外的噪声
print '求评论数平均数和方差，去掉三个方差之外的噪声'
sys.stdout.flush()
f=open(train_file_name,'r')
while 1:
	num+=1
	line=f.readline()
	if not line:
		break
		pass
	comm=int(line.split()[4])
	avar+=comm
	pass
avar=avar*1.0/num
print 'lines:%d'%num
f.seek(0)
while 1:
	line=f.readline()
	if not line:
		break
		pass
	comm=int(line.split()[4])
	D+=abs(comm-avar)**2*1.0/num
	pass
f.seek(0)
feature=[]
target=[]
fenci_str=''

# 处理基本特征
print '处理基本特征'
sys.stdout.flush()
while 1:
	line=f.readline()
	if not line:
		break
		pass
	comm=int(line.split()[4])
	if comm<=(avar-3*D) or comm>=(avar+3*D):
		continue
	target.append(comm)
	line,each_feature=get_feature(line,feature)
	# 重复增加若干倍
	times=0
	if comm<=5:
		times=1
		pass
	elif comm<=10:
		times=10
	elif comm<=50:
		times=50
	elif comm<=100:
		times=100
	else:
		times=200
	for i in range(times):
		fenci_str+=line
	pass
# 提取前50个关键词
print '提取前50个关键词'
sys.stdout.flush()
words=[]
freqs=[]
jieba.analyse.set_stop_words("stopwords")
tags = jieba.analyse.extract_tags(fenci_str, topK=50,withWeight=True)
fenci_str=""
for tag in tags:
	# print(tag[0]+str(tag[1]))
	words.append(tag[0])
	freqs.append(tag[1])

# 加入关键词特征
print '加入关键词特征'
sys.stdout.flush()
f.seek(0)
i=0
while 1:
	line=f.readline()
	if not line:
		break
		pass
	comm=int(line.split()[4])
	if comm<=(avar-3*D) or comm>=(avar+3*D):
		continue
	data=line.split()[7:]
	data=string.join(data,'-').strip()
	get_word_vector(data,feature[i])
	i+=1
	pass
f.close()
# 训练KNN
print '训练KNN'
sys.stdout.flush()
K=2
feature=numpy.array(feature)
target=numpy.array(target)
neigh=NearestNeighbors(n_neighbors=K)
neigh.fit(feature)
# 处理测试数据
# 暂时用训练数据的均值方差
print '处理测试数据'
sys.stdout.flush()
# 去掉噪声后的测试数据个数
test_num=0
# 所有测试数据个数
test_whole_num=0
num_1=0
num_2=0
num_3=0
num_4=0
num_5=0
corr_num=0
corr_num_1=0
corr_num_2=0
corr_num_3=0
corr_num_4=0
corr_num_5=0
test_feature=[]
t=open(test_file_name,'r')
while 1:
	line=t.readline()
	if not line:
		break
		pass
	test_whole_num+=1
	comm=int(line.split()[4])
	if comm<=(avar-3*D) or comm>=(avar+3*D):
		continue
	test_num+=1
	if comm<=5:
		num_1+=1
		pass
	elif comm<=10:
		num_2+=1
	elif comm<=50:
		num_3+=1
	elif comm<=100:
		num_4+=1
	else:
		num_5+=1
	line,each_feature=get_feature(line,test_feature)
	data=line.split()[7:]
	data=string.join(data,'-').strip()
	get_word_vector(data,each_feature)
	each_feature=numpy.array(each_feature)
	distence,index=neigh.kneighbors(each_feature)
	whole_distence=0.0
	# 先求总体距离，留待加权用
	for i in range(K):
		whole_distence=whole_distence+distence[0][i]
	predict_comm=0
	for i in range(K):
		this_index=index[0][i]
		if distence[0][i]==0.0:
			predict_comm=target[this_index]
			break
			pass
		else:
			predict_comm+=(1-distence[0][i]*1.0/whole_distence)*target[this_index]/(K-1)
	predict_comm=int(round(predict_comm))
	if predict_comm==comm:
		corr_num+=1
		if comm<=5:
			corr_num_1+=1
			pass
		elif comm<=10:
			corr_num_2+=1
		elif comm<=50:
			corr_num_3+=1
		elif comm<=100:
			corr_num_4+=1
		else:
			corr_num_5+=1
		pass
	pass
print '去噪声之后的正确率:%f'%(corr_num*1.0/test_num)
print '全部的正确率%f'%(corr_num*1.0/test_whole_num)
print 'first rate%f'%(corr_num_1*1.0/num_1)
print 'second rate%f'%(corr_num_2*1.0/num_2)
print 'third rate%f'%(corr_num_3*1.0/num_3)
print 'forth rate%f'%(corr_num_4*1.0/num_4)
print 'fifth rate%f'%(corr_num_5*1.0/num_5)

sys.stdout.flush()
