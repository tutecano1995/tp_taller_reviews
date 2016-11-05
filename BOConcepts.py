from gensim.models import Word2Vec
from sklearn.cluster import KMeans
from featurehash_y_tsne import *
import matplotlib as mpl
mpl.use('TkAgg')
import pylab as Plot
import csv
import random
import numpy as np
import json
import base64

def create_bag_of_centroids( wordlist, word_centroid_map ):
	#
	# The number of clusters is equal to the highest cluster index
	# in the word / centroid map
	num_centroids = max( word_centroid_map.values() ) + 1
	#
	# Pre-allocate the bag of centroids vector (for speed)
	bag_of_centroids = np.zeros( num_centroids, dtype="float32" )
	#
	# Loop over the words in the review. If the word is in the vocabulary,
	# find which cluster it belongs to, and increment that cluster count 
	# by one
	for word in wordlist:
		if word in word_centroid_map:
			index = word_centroid_map[word]
			bag_of_centroids[index] += 1
	#
	# Return the "bag of centroids"
	return bag_of_centroids

#Funcion muy cabeza que sirve para seleccionar aproximadamente 1500 de cada valor y que sirve solo para este caso, y que aproxima a una seleccion homogenea
#Le otorgo probabilidad 1500/#reviews_con_esa_estrella dependiendo de que estrella toca
#Para este caso el total de reviews por puntuación es: [ 37899,  21576,  30305,  56900, 260571]
def elegir_filas_estrellas_homogeneas_2(estrellas):
    contador_estrellas=np.array([0]*5)
    cant_reviews=len(estrellas)
    filas = []
    total = 0
    for i in xrange(len(estrellas)):
    	rand = random.uniform(0,1)
    	if int(estrellas[i]) == 1:
    		if rand<0.039: filas.append(i)
    	if int(estrellas[i]) == 2:
    		if rand<0.069: filas.append(i)
    	if int(estrellas[i]) == 3:
    		if rand<0.049: filas.append(i)
    	if int(estrellas[i]) == 4:
    		if rand<0.026: filas.append(i)
    	if int(estrellas[i]) == 5:
    		if rand<0.0057: filas.append(i)    		
    return filas

model = Word2Vec.load_word2vec_format("data/GoogleNews-vectors-negative300.bin",binary = True)
words = set()
reviews = {}
i = 0
with open('train.csv','r') as train_file:
	train_csv = csv.reader(train_file)
	next(train_csv)
	for row in train_csv:
			reviewid = row[0]
			predict = row[6]
			text = row[9]
			text_words = text.split(" ")
			if not(21<len(text_words)<223): continue
			reviews[reviewid] = {}
			reviews[reviewid]['text'] = text
			reviews[reviewid]['pred'] = predict
			if not i%10000: print(i)
			i+=1
			for word in text_words:
					words.add(word)

print("train.csv cargado!")

selected_vectors = np.empty((0,300))	#La longitud de los vectores en el modelo es de 300
word_index = []
i = 0
print("Comenzando filtrado de palabras")
for word in words:
	try:
		word_vector = model[word]
		selected_vectors = np.vstack((selected_vectors,word_vector))
		word_index.append(word)
	except:
		i+=1
		if not i%10000:	#Imprimo la cantidad de palabras "ausentes" cada mil
			print(i)


#NO SOMOS COMO SERVETTO, EL 99% DEL CODIGO ES DE ACA:
#https://www.kaggle.com/c/word2vec-nlp-tutorial/details/part-3-more-fun-with-word-vectors

print("Clustering - KMeans")
num_clusters = 100
kmeans_clustering = KMeans (n_clusters = num_clusters)
idx = kmeans_clustering.fit_predict(selected_vectors)
word_centroid_map = dict(zip(word_index,idx))

#Imprimo algunos clusters para ver que onda
print("Imprimimos algunos clusters")
for cluster in xrange(0,3):
	print ("\nCluster %d" % cluster)
	cluster_words = []
	for i in xrange(0,len(word_centroid_map.values())):
			if(word_centroid_map.values()[i] == cluster):
				cluster_words.append(word_centroid_map.keys()[i])
	print (cluster_words)

print("Hacemos BOCs")
i = 0
matriz_bocs = np.empty((0,num_clusters))
estrellas_bocs = []
for reviewid, review in reviews.iteritems():
	review['vec'] = create_bag_of_centroids(review['text'].split(" "),word_centroid_map)
	i+=1
	if not i%10000:	print (i) 
	matriz_bocs = np.vstack((matriz_bocs,review['vec']))
	estrellas_bocs.append(review['pred'])

#filas = elegir_filas_estrellas_homogeneas_2(estrellas_bocs)
filas = elegir_filas_random(matriz_bocs)
estrellas_seleccionadas = [int(estrellas_bocs[k]) for k in filas]
matriz_red = matriz_bocs[filas]

colourmap= {1:'#011f4b',2:'#03396c',3:'#005b96',4:'#6497b1',5:'#b3cde0'}
colours = [colourmap[n] for n in estrellas_seleccionadas]

print("Y ahora reducimos con tsne")
reduced_set =tsne(matriz_red,no_dims=2,initial_dims=20,perplexity=20.0,metric="cosine")

star_hist=np.array([0]*5)
for j in estrellas_seleccionadas:
    star_hist[j-1]+=1

Plot.scatter(reduced_set[:,0],reduced_set[:,1],c=colours_2,alpha=1,s=80,marker='.',lw=0)
Plot.show()


estrellas_seleccionadas=np.array(estrellas_seleccionadas)
with open("tsne_10k_random.json", 'w') as f:
    json.dump(reduced_set,f,cls=NumpyEncoder)

with open("tsne_10k_estrellas.json", 'w') as f:
    json.dump(estrellas_seleccionadas,f,cls=NumpyEncoder)
