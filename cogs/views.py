# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import generics
from rest_framework.response import Response
from ics.models import *
from basic.v11.serializers import AdjustmentHistorySerializer
from cogs.square.update_all_team_inventories import iso_format, update_all_team_inventories
from cogs.queries.integration_adjustments import adjust_inventory_using_stitch_csv


# Receives a list of Adjustments to add/subtract to current inventory (since square doesn't know Polymer's inventory),
# and creates a new Adjustment for each.
class CreateSquareAdjustments(generics.CreateAPIView):
  def post(self, request, *args, **kwargs):
    last_square_sync_times = dict(Team.objects.values_list('id', 'last_synced_with_square_at'))
    end_time = iso_format(timezone.now())
    failed_teams = update_all_team_inventories(last_square_sync_times, end_time)
    if failed_teams:
      message = "Square sync failed with teams: " + ", ".join(failed_teams)
      data = '{"message": "%s"}' % message
      return Response(data=data, status=500)
    Team.objects.update(last_synced_with_square_at=end_time)

    return Response(data='{"message": "Successfully made all adjustments."}', status=201)


class CreateCsvAdjustments(generics.CreateAPIView):
  def post(self, request, *args, **kwargs):
    polymer_team_id = request.data.get('team', None)
    if polymer_team_id is None:
      raise serializers.ValidationError('Request must include "team" data')
    new_adjustments = adjust_inventory_using_stitch_csv(int(polymer_team_id), request)
    if new_adjustments is None:
      raise serializers.ValidationError('Your team has not registered any data mapping the csv rows to Polymer inventory')
    serialized_adjustments = []
    for adjustment in new_adjustments:
      serialized_adjustments.append(AdjustmentHistorySerializer(adjustment).data)
    return Response(data=serialized_adjustments, status=201)
