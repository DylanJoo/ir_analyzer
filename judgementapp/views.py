# Create your views here.
from io import StringIO
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.template import Context, loader, RequestContext
# from django.core.servers.basehttp import FileWrapper
from django.shortcuts import render, get_object_or_404
from wsgiref.util import FileWrapper

import collections
from judgementapp.models import *
import json
from tqdm import tqdm

def index(request):
    queries = Query.objects.order_by('qId')
    output = ', '.join([q.text for q in queries])

    # template = loader.get_template('judgementapp/index.html')
    context = {'queries': queries}
    # return HttpResponse(template.render(request, context))
    return render(request, 'judgementapp/index.html', context)

def qrels(request):
    judgements = Judgement.objects.exclude(relevance=-1)

    response = HttpResponse(judgements, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=qrels.txt'
    return response

def qlabels(request):
    # queries = Query.objects.all()
    queries = Query.objects.exclude(text="NA")

    response = HttpResponse(queries, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=qlabels.jsonl'
    #response['X-Sendfile'] = myfile
    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    return response

def query_list(request):
    # see if we need to add the filter (about the judged)
    queries = Query.objects.order_by('id')
    return render(request, 'judgementapp/query_list.html', {'queries': queries})

def query(request, qId):
    query = Query.objects.get(qId=qId)
    judgements = Judgement.objects.filter(query=query.id)
    predictions_base = PredictionBase.objects.filter(query=query.id)
    predictions_compare = PredictionCompare.objects.filter(query=query.id)

    combined = zip(predictions_base, predictions_compare)

    if "clear" in request.POST:
        for c in query.category:
            query.category[c] = 0
        for c in query.topic:
            query.topic[c] = 0
        query.comment = ""

    else:
        if "csrfmiddlewaretoken" in request.POST:
            # category
            for c in query.category:
                if c in request.POST.getlist('category'):
                    query.category[c] = 1
                else:
                    query.category[c] = 0

            # topic
            for t in query.topic:
                if t in request.POST.getlist('topic'):
                    query.topic[t] = 1
                else:
                    query.topic[t] = 0

        if 'topic-drop' in request.POST:
            for t_sub in request.POST.getlist('topic-drop'):
                t, sub = t_sub.split('-')
                query.topic[t] = int(sub)

        if "comment" in request.POST:
            query.comment = request.POST['comment'].strip()

    query.save()
    query.length = len(query.text)

    # navigation
    prev = None
    try:
        prev = Query.objects.get(id=query.id-1)
    except:
        pass

    next = None
    try:
        next = Query.objects.get(id=query.id+1)
    except:
        pass

    return render(request, 'judgementapp/query.html', 
            {'query': query, 
             'judgements': judgements, 
             'combined': combined, 
             'prev': prev, 'next': next}
    )

def document(request, qId, docId):
    document = Document.objects.get(docId=docId)
    query = Query.objects.get(qId=qId)

    judgements = Judgement.objects.filter(query=query.id)
    judgement = Judgement.objects.filter(query=query.id, document=document.id)[0]
    rank = -1
    for (count, j) in enumerate(judgements):
        if j.id == judgement.id:
            rank = count+1
            break


    prev = None
    try:
        prev = Judgement.objects.filter(query=query.id).get(id=judgement.id-1)
    except:
        pass

    next_query = None
    next = None
    try:
        next = Judgement.objects.filter(query=query.id).get(id=judgement.id+1)
    except:
        try:
            next_query = Query.objects.get(id=query.id+1)
        except:
            pass

    content = document.get_content()

    return render(request, 'judgementapp/document.html', 
            {'document': document, 'query': query, 
                'judgement': judgement, 'next': next, 'prev': prev, 
                'rank': rank, 'total_rank': judgements.count(), 
                'next_query': next_query,
                'content': content})

def judge(request, qId, docId):
    query = get_object_or_404(Query, qId=qId)
    document = get_object_or_404(Document, docId=docId)
    relevance = request.POST['relevance']
    comment = request.POST['comment'].strip()

    judgements = Judgement.objects.filter(query=query.id)
    judgement, created = Judgement.objects.get_or_create(query_id=query.id, document_id=document.id)
    judgement.relevance = int(relevance)
    # if comment != '':
    #     judgement.comment = comment
    judgement.comment = comment
    judgement.save()


    next = None
    try:
        next = Judgement.objects.filter(query=query.id).get(id=judgement.id+1)
        if 'next' in request.POST:
            document = next.document
            judgement = next
            next = Judgement.objects.filter(query=query.id).get(id=judgement.id+1)
    except:
        pass

    prev = None
    try:
        prev = Judgement.objects.filter(query=query.id).get(id=judgement.id-1)
    except:
        pass

    rank = -1
    for (count, j) in enumerate(judgements):
        if j.id == judgement.id:
            rank = count+1
            break


    content = document.get_content()

    # return render(request, 'judgementapp/upload.html', context)
    return render(request, 'judgementapp/document.html', 
            {'document': document, 'query': query, 
                'judgement': judgement, 'next': next, 'prev': prev, 
                'rank': rank, 'total_rank': judgements.count(), 
                'content': content
            }) 


def reset(request):
    # remove queries
    queries = Query.objects.all()
    n = len(queries)
    queries.delete()

    Judgement.objects.all().delete()
    PredictionBase.objects.all().delete()
    PredictionCompare.objects.all().delete()

    return render(request, 'judgementapp/upload.html', {
        "deleted": False, "amount": n
    })

def delete(request):
    # remove results
    judgements = Judgement.objects.filter(relevance=-1)
    n = len(judgements)
    judgements.delete()

    return render(request, 'judgementapp/upload.html', {
        "deleted": True, "amount": n
    })

def upload(request):
    context = {}

    if 'queryFile' in request.FILES:
        f = request.FILES['queryFile']
        qryCount = 0
        for i, query in enumerate(f):
            data = json.loads(query)
            qid = data['_id']
            content = data['text']
            query, created = Query.objects.get_or_create(qId=qid)

            if created:
                query.text = content
                query.save()
                qryCount += 1

        context['uploaded'] = True
        context['queries'] = qryCount

        return render(request, 'judgementapp/upload.html', context)

    if 'qrelsFile' in request.FILES:
        f = request.FILES['qrelsFile']

        judCount = 0
        qrels = collections.defaultdict(list)
        for line in f:
            qid, _, docid, rel = line.split()
            # qrels[qid.decode("utf-8")].append((docid.decode("utf-8"), rel))
            qrels[qid.decode("utf-8")].append((docid.decode("utf-8"), rel))

        for qid in tqdm(qrels):
            query = Query.objects.get(qId=qid)
            for docid, rel in qrels[qid]:
                document, _ = Document.objects.get_or_create(docId=docid)
                document.text = "NA"
                document.save()
                judgement, _ = Judgement.objects.get_or_create(query_id=query.id, document_id=document.id)
                judgement.relevance = int(rel)
                judgement.save()
                judCount += 1

        context['uploaded'] = True
        context['judgements'] = judCount

        return render(request, 'judgementapp/upload.html', context)

    if ('resultsFile0' in request.FILES) or ('resultsFile1' in request.FILES):
        result_id = list(request.FILES.keys())[0]
        Prediction = {'resultsFile0': PredictionBase, 
                      'resultsFile1': PredictionCompare}[result_id]

        f = request.FILES[result_id]
        qryCount, docCount, prdCount = 0, 0, 0

        for result in tqdm(f):
            qid, z, docid, rank, score, desc = result.decode().strip().split()

            if int(rank) <= 50:
                query = Query.objects.get(qId=qid)
                document, _ = Document.objects.get_or_create(docId=docid)

                # add to predictions
                prediction, _ = Prediction.objects.get_or_create(query_id=query.id, document_id=document.id)
                prediction.ranking = int(rank)

                # check judgement 
                judgement, created = Judgement.objects.get_or_create(query_id=query.id, document_id=document.id)
                if created:
                    judgement.relevance = -1
                    judgement.save()
                else:
                    prediction.relevance = judgement.relevance

                prediction.save()
                prdCount += 1
                
        context['uploaded'] = True
        context['documents'] = 0
        context['predictions'] = prdCount
        context['invalid_queries'] = qryCount

    return render(request, 'judgementapp/upload.html', context)
