REMOVE_ID_FROM_ALL_TASKS_IN_DB_WHICH_HAVE_IT = """UPDATE ics_task
							SET flagged_ancestors_id_string = (CASE WHEN task_with_ancestor_id.new_ancestors_string = '|' THEN '' ELSE task_with_ancestor_id.new_ancestors_string END)
							FROM (select
										id,
										flagged_ancestors_id_string,
										substring(flagged_ancestors_id_string from 0 for ancestor_id_position) || '|' || substring(flagged_ancestors_id_string from ancestor_id_position + %s) as new_ancestors_string
										from (
										select
											id,
											flagged_ancestors_id_string,
											strpos(flagged_ancestors_id_string, %s) AS ancestor_id_position
										from ics_task
										where strpos(flagged_ancestors_id_string, %s) > 0
										) task
							) task_with_ancestor_id
							WHERE ics_task.id = task_with_ancestor_id.id"""


REMOVE_ID_FROM_ALL_SPECIFIED_TASKS_WHICH_HAVE_IT = """UPDATE ics_task
							SET flagged_ancestors_id_string = (CASE WHEN task_with_ancestor_id.new_ancestors_string = '|' THEN '' ELSE task_with_ancestor_id.new_ancestors_string END)
							FROM (select
										id,
										flagged_ancestors_id_string,
										substring(flagged_ancestors_id_string from 0 for ancestor_id_position) || '|' || substring(flagged_ancestors_id_string from ancestor_id_position + %s) as new_ancestors_string
										from (
										select
											id,
											flagged_ancestors_id_string,
											strpos(flagged_ancestors_id_string, %s) AS ancestor_id_position
										from ics_task
										where strpos(flagged_ancestors_id_string, %s) > 0 and id = ANY(%s)
										) task
							) task_with_ancestor_id
							WHERE ics_task.id = task_with_ancestor_id.id"""
