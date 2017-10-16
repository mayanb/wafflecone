from rest_framework import serializers
from ics.models import *
from django.contrib.auth.models import User
from uuid import uuid4
from django.db.models import F, Sum, Max
from datetime import date, datetime, timedelta

class UserDetailSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='userprofile.team.name')
	team = serializers.CharField(source='userprofile.team.id', read_only=True)
	account_type = serializers.CharField(source='userprofile.account_type', read_only=True)
	profile_id = serializers.CharField(source='userprofile.id')

	class Meta:
		model = User
		fields = ('profile_id', 'username', 'first_name', 'last_name', 'team', 'account_type', 'team_name', )

class UserProfileSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='team.name')
	team = serializers.CharField(source='team.id', read_only=True)
	profile_id = serializers.CharField(source='id')
	username = serializers.CharField(source='user.username')
	first_name = serializers.CharField(source='user.first_name')
	last_name = serializers.CharField(source='user.last_name')

	class Meta:
		model = UserProfile
		fields = ('id', 'profile_id', 'username', 'first_name', 'last_name', 'team', 'account_type', 'team_name', )

class UserProfileCreateSerializer(serializers.ModelSerializer):
  username = serializers.CharField(source='user.username')
  password = serializers.CharField(source='user.password')
  first_name = serializers.CharField(source='user.first_name')
  team_name = serializers.CharField(source='team.name', read_only=True)
  profile_id = serializers.CharField(source='id', read_only=True)

  def create(self, validated_data):
    data = validated_data.get('user')
    user = User.objects.create(**data)
    user.set_password(data.get('password'))
    user.save()

    team = validated_data.get('team')
    account_type = validated_data.get('account_type', '')
    userprofile = UserProfile.objects.create(
    	user=user, 
    	gauth_access_token="", 
    	gauth_refresh_token="", 
    	token_type="", 
    	team=team,
    	account_type=account_type,
    )
    return userprofile

  class Meta:
    model = UserProfile
    extra_kwargs = {'account_type': {'write_only': True}, 'password': {'write_only': True}}
    fields = ('id', 'profile_id', 'username', 'password', 'first_name', 'team', 'account_type', 'team_name', )


class TeamSerializer(serializers.ModelSerializer):
	users = UserProfileSerializer(source='userprofiles', many=True, read_only=True)

	class Meta:
		model = Team
		fields = ('id', 'name', 'users')