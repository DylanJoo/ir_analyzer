import json
from django.conf import settings
from django.db import models

label2topic = {
        1: "Business",
        2: "Risk",
        3: "Legal",
        4: "Financial Status",
        5: "Strategic Plan",
        6: "Operataionl",
}

label2category = {
        0: "trivial",
        1: "company-specific",
        2: "change/action",
        3: "reason",
        4: "redirect",
}

# Create your models here.
class Document(models.Model):
	docId = models.CharField(max_length=100)
	text = models.TextField()
	# add document

	def __str__(self):
		return self.docId

	def get_content(self):
	    content = ""
	    with open(settings.DATA_DIR+"/"+self.docId) as f:
	        read = f.read()
	        data = json.loads(read)
	        self.text = data['metadata']['title']
	        content = data['contents']
	        self.save()
	    return content


def default_query_categories():
    return {str(i): 0 for i in label2category}

def default_query_topics():
    return {str(i): 0 for i in label2topic}

class Query(models.Model):
	# qId = models.IntegerField()
	qId = models.CharField(max_length=100)
	text = models.CharField(max_length=250, default="NA")
	category = models.JSONField(default=default_query_categories)
	comment = models.TextField(default="", null=True)
	topic = models.JSONField(default=default_query_topics)
	metadata = models.TextField()

	def __str__(self):
		# categories = " ".join(self.category.values())
		data_dict = {"id": self.qId, "text": self.text}
		to_return = json.dumps(data_dict)
		return to_return + '\n'

	def num_unjudged_docs(self):
		unjugded = [judgement for judgement in self.judgements() if judgement.relevance < 0]
		return len(unjugded)

	def num_judgements(self):
		return len(self.judgements())

	def judgements(self):
		return Judgement.objects.filter(query=self.id)

class PredictionCompare(models.Model):

	query = models.ForeignKey(Query, on_delete=models.CASCADE)
	document = models.ForeignKey(Document, on_delete=models.CASCADE)
	comment = models.TextField(default="", null=True)
	ranking = models.IntegerField(default=0)
	relevance = models.IntegerField(default=-1)

class PredictionBase(models.Model):

	query = models.ForeignKey(Query, on_delete=models.CASCADE)
	document = models.ForeignKey(Document, on_delete=models.CASCADE)
	comment = models.TextField(default="", null=True)
	ranking = models.IntegerField(default=0)
	relevance = models.IntegerField(default=-1)


class Judgement(models.Model):

	labels = {-1: 'Unjudged', 0: 'Not relvant', 1: 'Somewhat relevant', 2:'Highly relevant'}

	query = models.ForeignKey(Query, on_delete=models.CASCADE)
	document = models.ForeignKey(Document, on_delete=models.CASCADE)
	comment = models.TextField(default="", null=True)
	relevance = models.IntegerField(default=-1)

	def __str__(self):
		return '%s Q0 %s %s\n' % (self.query.qId, self.document.docId, self.relevance)

	def label(self):
		return self.labels[self.relevance]

