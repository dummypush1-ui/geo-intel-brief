"""Query-shaped candidates and fail-closed supplied explain review, no provisioning."""
from copy import deepcopy
INDEXES=(
 ('article_score_published_id', [('score',-1),('published',-1),('_id',-1)]),
 ('article_published_id', [('published',-1),('_id',-1)]),
 ('article_title_id', [('title',1),('_id',1)]),
 ('article_unsent_order', [('emailed',1),('score',-1),('published',-1),('_id',-1)]),
 ('article_critical_created_score', [('risk_level',1),('created_at',-1),('score',-1)]),
 ('article_created_id', [('created_at',-1),('_id',-1)]),
 ('article_category_export_id', [('category',1),('_id',1)]),
)
def query_plan():
 return {'scope':'candidate_not_provisioned','indexes':[{'collection':'articles','name':n,'keys':deepcopy(k),'options':{}} for n,k in INDEXES],
 'requires':['existing_index_names_options_collations','duplicates_and_field_type_audit','actual_query_explain_on_target','storage_and_write_cost_review','separate_provisioning_permission'],
 'provision_allowed':False,'ttl_allowed':False,'export_snapshot_consistent':False,
 'unsent_note':'Existing emailed $ne true is preserved; low selectivity may need schema migration, not assumed covered by index.',
 'general_category_note':'GENERAL includes null/missing via $or; candidate category/_id index needs actual explain, not assumed coverage.',
 'range_sort_note':'critical/weekly range plus score sort may require blocking sort; actual explain must validate costs.'}
def explain_review(receipt,max_examined=10000):
 if type(receipt) is not dict or set(receipt)!={'query_id','executionStats'} or type(receipt['query_id']) is not str or not receipt['query_id']:
  raise ValueError('Scoped supplied execution receipt required')
 s=receipt['executionStats'];keys={'executionSuccess','nReturned','totalKeysExamined','totalDocsExamined'}
 if type(s) is not dict or not keys<=set(s) or s['executionSuccess'] is not True:raise ValueError('Successful supplied execution stats required')
 if type(max_examined) is not int or not 1<=max_examined<=100000:raise ValueError('Invalid review bound')
 if any(type(s[k]) is not int or s[k]<0 for k in keys-{'executionSuccess'}):raise ValueError('Invalid supplied counters')
 return {'scope':'supplied_not_live_verified','query_id':receipt['query_id'],'within_review_bound':max(s['totalKeysExamined'],s['totalDocsExamined'])<=max_examined,'provision_allowed':False}
