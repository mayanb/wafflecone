import os
import sys
import boto3

waffle_envs = {k: v for k, v in os.environ.iteritems() if (k.startswith('WAFFLE_') or k.startswith('OAUTHLIB'))}

env = sys.argv[1]

if env == 'staging':
	prefix = 'STAGING'
elif env == 'production':
	prefix = 'PRODUCTION'

specific_envs = {k: v for k, v in os.environ.iteritems() if k.startswith(prefix + '_WAFFLE_')}

for k in specific_envs.keys():
	true_name = k.split(prefix + '_')[1]
	waffle_envs[true_name] = specific_envs[k]

client = boto3.client(
	'lambda',
	region_name='us-west-1',
	aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
)

function_name = 'wafflecone-{0}'.format(env)

environment = {
	'Variables': waffle_envs
}

client.update_function_configuration(FunctionName=function_name, Environment=environment)


