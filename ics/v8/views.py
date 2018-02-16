from rest_framework import generics
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from ics.v8.serializers import *
from ics.paginations import *
from ics.v8.queries import *

class TaskFilter(django_filters.rest_framework.FilterSet):
  created_at = django_filters.DateFilter(name="created_at", lookup_expr="startswith")
  class Meta:
      model = Task
      fields = ['created_at', 'is_open']

# tasks/
class TaskList(generics.ListAPIView):
  serializer_class = TaskSerializer
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_class = TaskFilter
  ordering_fields = ('updated_at', 'created_at', 'label_index', 'process_type__x')
  pagination_class = SmallPagination

  def get_queryset(self):
    return get_tasks(self.request.query_params)


'''
-----------------
API SPEC:
- Required endpoints to duplicate effect of /tasks/v7/ through multiple requests:
  -- /tasks/ : list of tasks
  -- /tasks/{task_id}/ : single task 
  -- /task-inputs/{task_id}/ : inputs for a single task
  -- /task-items/{task_id}/ : items/outputs for a single task 
  -- /task-attribute-values/{task_id}/ : task_attributes for a single task
  -- /process-type-attributes/{process_type}/ : attributes for a single process_type

- Then in the frontend, we would only need /tasks/ to render Main.js
- We would need to call /task-attribute-values/ and /process-type-attributes/ to render Task.js
- We would need /task-items/ and/or /task-inputs/ to render QRScanner.js
- Right??? Hmmm

'''





