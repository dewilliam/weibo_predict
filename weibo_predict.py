#!/usr/bin/env python
# -*- coding: utf-8 -*-
import string
import math
import sys
import re
import jieba
import jieba.analyse
from time import clock
import time
from sklearn.neighbors import NearestNeighbors


def get_feature_target(line):
	# 抽取目标值：转发数、评论数、点赞数
	# target_comm.append(int(line.split()[4]))
	# target_retweet.append(int(line.split()[5]))
	# target_like.append(int(line.split()[6]))
	each_target=[]
	each_target.append(int(line.split()[4]))
	each_target.append(int(line.split()[5]))
	each_target.append(int(line.split()[6]))
	# 统计表情个数
	face_num=line.count('[')
	# 清除表情信息
	for i in range(0,face_num):
		start_pos=line.find('[')
		if start_pos>0:
			end_pos=line.find(']',start_pos)
			if end_pos>0:
				# 多个相同的表情可一次删除
				line=line.replace(line[start_pos:end_pos+1],'')
				pass
			pass
	# if face_num:
	# 	line=re.sub('[(.*?)]','',line)
	# 	pass
	#清理url信息
	http_num=line.count('http://')
	https_num=line.count('https://')
	http_num=http_num+https_num
	if http_num:
		line=re.sub('http[s]*://(.*)/[a-zA-Z0-9]+','',line)
		pass
	# 清除官微信息
	# 两种情况，一种是“分享自”另一种是“来自”开头
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
	# 一些特殊噪声要处理的
	line=re.sub('@RAIN-JIHOON','',line)
	line=re.sub('@支付宝钱包','',line)
	# 开始统计各种特征
	each_feature=[]
	# hash_tag（#）的数量
	hash_tag_num=line.count('#')/2
	each_feature.append(hash_tag_num)
	# 发布时间的小时特征
	hour=int(line.split()[3].split(':')[0])*1.0/24
	each_feature.append(hour)
	# 是否有标题
	has_title=line.count('【')
	each_feature.append(has_title)
	# 表情数量特征
	each_feature.append(face_num)
	# URL数量特征
	each_feature.append(http_num)
	# @数量特征
	at_num=line.count('@')
	each_feature.append(at_num)
	# 字符串长度特征
	str_len=len(line)*1.0/140
	each_feature.append(str_len)
	return each_feature,each_target,line

# 构建每条微博的50个词汇的向量
# 加入用户的特征：平均互动数，发微博频率
def word_vector_user_info(data,this_feature):
	content=data.split()[7:]
	content=string.join(content,'-').strip()
	for j in range(0,50):
		word=words[j].encode('utf-8')
		word_count=content.count(word)
		word_freq=word_count*freqs[j]
		this_feature.append(word_freq)
		pass
	user_id=data.split()[0]
	if user_info.has_key(user_id):
		weibo_num=user_info[user_id]['weibo_num']
		avar_num_comm=user_info[user_id]['avar_num_comm']
		avar_num_retweet=user_info[user_id]['avar_num_retweet']
		avar_num_like=user_info[user_id]['avar_num_like']
	else:
		weibo_num=0
		avar_num_comm=0.0
		avar_num_retweet=0.0
		avar_num_like=0.0
	this_feature.append(weibo_num)
	this_feature.append(avar_num_comm)
	this_feature.append(avar_num_retweet)
	this_feature.append(avar_num_like)

print '开始.... %s'%str(time.asctime(time.localtime(time.time())))
sys.stdout.flush()
start=clock()
trian_data=[]
feature=[]
target_comm=[]
target_retweet=[]
target_like=[]
# 建立一个字典，用来存储用户的微博个数，平均互动数
# 每一个元素格式为：user_id:{weibo_num:num,avar_num:num}
user_info={}
total_weibo_num=0
fenci_str=""
trian_file=open('train_train_data','r')
num=0
while 1:
# for i in range(1000):
	num=num+1
	line=trian_file.readline()
	if not line:
		break
	# 执行get_feature_target函数，获得特征和目标值
	each_feature,each_target,changed_line=get_feature_target(line)
	# 把每个特征向量加入到特征矩阵中
	feature.append(each_feature)
	# 把训练数据的目标值放到相应的向量中
	target_comm.append(each_target[0])
	target_retweet.append(each_target[1])
	target_like.append(each_target[2])
	trian_data.append(line)
	# 把每条微博内容加到fenci_str中，用于提取前50个词
	content=line.split()[7:]
	content=string.join(content,'-')[:].strip()
	fenci_str=fenci_str+content
	# 处理用户平均互动数（这里只统计了评论数）和用户发微博的总数
	user_id=str(line.split()[0])
	user_comm_num=int(line.split()[4])
	user_retweet_num=int(line.split()[5])
	user_like_num=int(line.split()[6])
	if user_info.has_key(user_id):
		user_info[user_id]['weibo_num']=user_info[user_id]['weibo_num']+1
		# 现在只把所有互动数加起来，所有微博信息遍历之后，再计算平均值
		user_info[user_id]['avar_num_comm']=user_info[user_id]['avar_num_comm']+user_comm_num
		user_info[user_id]['avar_num_retweet']=user_info[user_id]['avar_num_retweet']+user_retweet_num
		user_info[user_id]['avar_num_like']=user_info[user_id]['avar_num_like']+user_like_num
		pass
	else:
		user_info.setdefault(user_id,{'weibo_num':1,'avar_num_comm':user_comm_num,'avar_num_retweet':user_retweet_num,'avar_num_like':user_like_num})
	total_weibo_num=total_weibo_num+1

finish_1=clock()
print "特征第一部分处理完毕。。。训练数据%d条time:%s"%(num,str(finish_1-start))
sys.stdout.flush()
# 处理平均互动数，把字典user_info 中的所有avar_num设置成avar_num/weibo_num
# 发微博的频率定义为某用户发布的微博的个数除以总体训练数据的微博总数
for k in user_info.keys():
	user_info[k]['avar_num_comm']=user_info[k]['avar_num_comm']*1.0/user_info[k]['weibo_num']
	user_info[k]['avar_num_retweet']=user_info[k]['avar_num_retweet']*1.0/user_info[k]['weibo_num']
	user_info[k]['avar_num_like']=user_info[k]['avar_num_like']*1.0/user_info[k]['weibo_num']
	user_info[k]['weibo_num']=user_info[k]['weibo_num']*1.0/total_weibo_num
finish_2=clock()
print "平均互动数处理完毕。。。time:%s"%str(finish_2-start)
sys.stdout.flush()
# 提取前50个关键词
words=[]
freqs=[]
jieba.analyse.set_stop_words("stopwords")
tags = jieba.analyse.extract_tags(fenci_str, topK=50,withWeight=True)
for tag in tags:
	# print(tag[0]+str(tag[1]))
	words.append(tag[0])
	freqs.append(tag[1])
fenci_str=""
finish_3=clock()
print "提取50个关键词处理完毕。。。time:%s"%str(finish_3-start)
sys.stdout.flush()

# 构建每条微博的50个词汇的向量
# 加入用户的特征：平均互动数，发微博频率
i=0
for data in trian_data:
	word_vector_user_info(data,feature[i])
	i=i+1

finish_4=clock()
print '特征提取完毕。。。time:%s'%str(finish_4-start)
sys.stdout.flush()

# 开始训练模型
# M为距离加权平均中控制左右扩展的参数
K=2
M=5
print '开始训练模型,%s'%str(time.asctime(time.localtime(time.time())))
print '模型用的KNN，找到最近的K的点，求距离加权平均作为测试数据的目标值'
print 'K=%d,M=%d'%(K,M)
sys.stdout.flush()
neigh=NearestNeighbors(n_neighbors=K)
neigh.fit(feature[:200])
# distence,index=neigh.kneighbors(feature[100])
print '把测试数据生成测试向量,%s'%str(time.asctime(time.localtime(time.time())))
sys.stdout.flush()
# 总体测试数据微博数量
total_test_num=0
# 预测正确的微博数量
comm_corr_num=0
retweet_corr_num=0
like_corr_num=0
D_comm=0.0
D_retweet=0.0
D_like=0.0
total_truth_comm=0
total_truth_retweet=0
total_truth_like=0
test_file=open('train_test_data','r')
print '加权平均公式为：Σ(1-this_d/whole_d)*this_target/K'
sys.stdout.flush()
test_num=0
while 1:
# for zz in range(1000):
	test_num=test_num+1
	line=test_file.readline()
	if not line:
		break
		pass
	each_feature,each_target,changed_line=get_feature_target(line)
	word_vector_user_info(changed_line,each_feature)
	distence,index=neigh.kneighbors(each_feature)
	this_target=0
	whole_distence=0.0
	# 先求总体距离，留待加权用
	for i in range(K):
		whole_distence=whole_distence+distence[0][i]
	# 加权平均公式为：Σ(1-this_d/whole_d)*this_target/K
	for i in range(K):
		# 如果有一个训练数据和测试数据相等，则直接把测试数据预测成该训练数据的目标值
		# 否则按照距离加权平均去计算目标值
		this_target_comm=0
		this_target_retweet=0
		this_target_like=0
		this_index=index[0][i]
		if distence[0][i]==0.0:
			this_target_comm=target_comm[this_index]
			this_target_retweet=target_retweet[this_index]
			this_target_like=target_like[this_index]
			break
			pass
		else:
			this_target_comm=this_target_comm+(1-distence[0][i]/whole_distence)*target_comm[this_index]/K
			this_target_retweet=this_target_retweet+(1-distence[0][i]/whole_distence)*target_retweet[this_index]/K
			this_target_like=this_target_like+(1-distence[0][i]/whole_distence)*target_like[this_index]/K
		pass
	#this_target_XXX就是预测出的目标值
	# truth_XXX为可以视为正确的预测值的左右置信区间长度
	if each_target[0]>0:
		truth_comm=(math.pow(10,math.ceil(math.log(each_target[0],10)))-math.pow(10,math.floor(math.log(each_target[0],10))))/M
		pass
	else:
		truth_comm=9.0/M
	if each_target[1]>0:
		truth_retweet=(math.pow(10,math.ceil(math.log(each_target[1],10)))-math.pow(10,math.floor(math.log(each_target[1],10))))/M
		pass
	else:
		truth_retweet=9.0/M
	if each_target[2]>0:
		truth_like=(math.pow(10,math.ceil(math.log(each_target[2],10)))-math.pow(10,math.floor(math.log(each_target[2],10))))/M
		pass
	else:
		truth_like=9.0/M
	total_truth_comm=total_truth_comm+truth_comm/2/each_target[0]
	total_truth_retweet=total_truth_retweet+truth_retweet/2/each_target[1]
	total_truth_like=total_truth_like+truth_like/2/each_target[2]
	# 在区间内就正确数量加一
	# this_target_comm=round(this_target_comm)
	# this_target_retweet=round(this_target_retweet)
	# this_target_like=round(this_target_like)
	if this_target_comm>=(each_target[0]-truth_comm) and this_target_comm<=(each_target[0]+truth_comm):
		comm_corr_num=comm_corr_num+1
		pass
	if this_target_retweet>=(each_target[1]-truth_retweet) and this_target_retweet<=(each_target[1]+truth_retweet):
		retweet_corr_num=retweet_corr_num+1
		pass
	if this_target_like>=(each_target[2]-truth_like) and this_target_like<=(each_target[2]+truth_like):
		like_corr_num=like_corr_num+1
		pass
	# 总体测试数量加一
	total_test_num=total_test_num+1
	#方差
	D_comm=D_comm+(each_target[0]-this_target_comm)**2
	D_retweet=D_retweet+(each_target[1]-this_target_retweet)**2
	D_like=D_like+(each_target[2]-this_target_like)**2
	pass
print '测试数据处理完毕。。。测试数据%d条time:%s'%(test_num,str(time.asctime(time.localtime(time.time()))))
print '输出正确率'
sys.stdout.flush()
comm_corr_rate=comm_corr_num*1.0/total_test_num
retweet_corr_rate=retweet_corr_num*1.0/total_test_num
like_corr_rate=like_corr_num*1.0/total_test_num

##
D_comm=D_comm**0.5*1.0/total_test_num
D_retweet=D_retweet**0.5*1.0/total_test_num
D_like=D_like**0.5*1.0/total_test_num
total_truth_comm=total_truth_comm*1.0/total_test_num
total_truth_retweet=total_truth_retweet*1.0/total_test_num
total_truth_like=total_truth_like*1.0/total_test_num
print '评论数预测正确率为：%f'%comm_corr_rate
print '转发数预测正确率为：%f'%retweet_corr_rate
print '点赞数预测正确率为：%f'%like_corr_rate
print '评论数方差为：%f'%D_comm
print '转发数方差为：%f'%D_retweet
print '点赞数方差为：%f'%D_like
print '评论数置信区间长度为：%f'%total_truth_comm
print '转发数置信区间长度为：%f'%total_truth_retweet
print '点赞数置信区间长度为：%f'%total_truth_like
sys.stdout.flush()
print '\n\n'


#.....................................finished..........................................
finish_5=clock()
print 'finished.... %s,total time:%s'%(str(time.asctime(time.localtime(time.time()))),str(finish_5-start))
print '\n\n\n\n\n\n'
sys.stdout.flush()
