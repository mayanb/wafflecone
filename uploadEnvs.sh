# get the right lambda function based on the param
_env=$1

# find all the relevant environment variables
_vars=''
while IFS='=' read -r name value ; do
	if [[ $name =~ 'WAFFLE_'([a-zA-Z0-9_])+ ]];
	then
	  _vars+=$name=${!name},
	fi
done < <(env)

# remove trailing comma
_vars=${_vars%?}

# add curly braces
_vars={$_vars}

aws --region us-west-1 lambda update-function-configuration --function-name wafflecone-$_env --environment Variables="$_vars"
