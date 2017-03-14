import React from 'react';
import $ from 'jquery';
import TableList from './Tables.jsx';
import ActivityLog from './ActivityLog.jsx';
import { Filters } from './Inputs.jsx';
import { ContentDescriptor } from './Layout.jsx'
import moment from 'moment'
import TaskDialog from './TaskDialog.jsx'
import update from 'immutability-helper';

function NoResults(props) {
  return (
    <div className="noresults">
      <span>Looks like there's nothing here. Try expanding your search.</span>
    </div>
  )
}

export default class Tasks extends React.Component {
  constructor(props) {
    super(props);
    this.handleFilter = this.handleFilter.bind(this)
    this.handleTaskToggle = this.handleTaskToggle.bind(this)
    this.handleTaskChanged = this.handleTaskChanged.bind(this)
    this.state = {

    	inventory: props.inventory,
      activeTask: null,

      tasks: [],
      taskGroups: {},
      processes: {},
      products: {},

      loading: false,
      mounted: false, 

      activeFilters: this.props.filters
    };
  }


	render() {
    console.log(this.state.activeFilters)
    if (!window.history.state) {
      window.history.replaceState(this.state.activeFilters, "Scoop @ bama", window.location.href);
    }

    var panel = (
      <div style={{display: this.state.loading?"block":""}} className="loading">
            <div className="spinner"></div>
          </div>
    )

    if (!this.state.loading && this.state.inventory && this.state.tasks.length > 0) {
      panel = (
        <TableList 
            taskGroups={this.state.taskGroups} 
            processes={this.state.processes}
            inventory={this.props.inventory}
            onTaskClick={this.handleTaskToggle}
          />
      )
    }

    else if (!this.state.loading && this.state.tasks.length > 0) {
      panel = (
        <ActivityLog
          tasks={this.state.tasks}
          processes={this.state.processes}
          inventory={this.props.inventory}
          onTaskClick={this.handleTaskToggle}
        />
      )
    }

    else if (!this.state.loading) {
      panel = <NoResults />
    }

    let obj = false;
		if (Object.keys(this.state.processes).length === 0 && this.state.processes.constructor === Object) {

		} else {
      obj = 
        <div className="content">
          <TaskDialog 
            active={(this.state.activeTask != null)} 
            task={this.state.activeTask}
            onTaskClose = {this.handleTaskToggle}
            onTaskChanged={this.handleTaskChanged}
          />

          <Filters
            label = {this.state.activeFilters.label}
            filters = {this.state.activeFilters}
            active = {this.state.activeFilters.active}
            processes={this.state.processes} 
            products={this.state.products} 
            dates={this.props.inventory==false}
            onFilter={(object) => this.handleFilter(object, true)}
            initialDates={{start: this.state.activeFilters.start, end: this.state.activeFilters.end}}
          />

          {panel}


        </div>

    }

		return ( 
			<div>
				{obj}
	    </div>
	  )
  }

  componentWillReceiveProps(np) {
    if (!this.mounted) {
      return 
    }
    if (np.filters == null || (Object.keys(np.filters).length === 0 && np.filters.constructor === Object)) {
      return
    }

    this.setState({activeFilters : np.filters}, function () {
      this.handleFilter({}, false)
    })

  }

  handleTaskToggle(task) {
    if (this.state.activeTask == null) {
      this.setState({activeTask: task})
    } else {
      this.setState({activeTask: null})
    }
  }

  handlePage(x) {
    var thisObj = this
    var newState = {}
    var defs = [this.getTasks(newState, x, this.props.inventory)]

    $.when.apply(null, defs).done(function() {
      if (x < thisObj.state.currentPage) {
        newState.startIndex = thisObj.state.startIndex - newState.count

      } else {
        newState.startIndex = thisObj.state.startIndex + thisObj.state.count
      }
      newState.currentPage = x
      if (newState.currentPage == "2") {
        newState.previous = "1"
      }
      thisObj.setState(newState)
    });    
  }

  componentDidMount() {
    var newState = { tasks: [], taskGroups: {}, processes: {}, products: {} };
    var defs = []

    defs.push(this.getProcesses(newState));
    defs.push(this.getProducts(newState));

    var component = this

    $.when.apply(null, defs).done(function() {
      
      // apply the processes/products state
      component.setState(newState)

      // update the processes and product filters
      let af = component.state.activeFilters
      console.log(af)

      let ns = update(af, {
        $merge: {
          processes: component.matchByID(af.processes || [], newState.processes),
          products: component.matchByID(af.products || [], newState.products)
        }
      })

      component.setState({activeFilters: ns})


      // get the tasks
      var d2 = [component.getTasks(newState, -1, component.props.inventory)]
      $.when.apply(null, d2).done(function() {
        newState.mounted = true
        component.setState(newState)
      });
    })
  }

  matchByID(select, data) {
    let ns = select.map(function (id) {
      return { value: id, label: data[id].name }
    })

    return ns
  }

  handleTaskChanged(task) {
    let url = window.location.origin + "/ics/tasks/" + task.id + "/"
    let thisObj = this
    $.get(url)
      .done(function (data) {
        let taskGroup = getSemanticTaskGroup(data, thisObj.state.processes)

        // the jankiest loop there ever was....
        let i = -1
        let group = thisObj.state.taskGroups[taskGroup].tasks

        for(var j = 0; j < group.length; j++) {
          if (group[j].id == data.id) {
            i = j
            break
          }
        }

        if (i == -1) return 

        // now lets make a new state
        var ns = update(thisObj.state, {
          taskGroups: {
            [taskGroup]: { 
              tasks : {
                [i] : {
                  $set: data
                }
              }
            }
          }, activeTask : {$set: data}
        })

        thisObj.setState(ns)

      })
  }

  getTasks(container, page, inventory) {
    var deferred = $.Deferred();

    var url = window.location.origin + "/ics/tasks/"

    let filters = this.parseFilters()
    filters.dashboard = "True"

    var processes = this.state.processes
    if (Object.keys(this.state.processes).length === 0 && this.state.processes.constructor === Object)
      processes = container.processes

    this.setState({loading: true})
    let thisObj = this

    $.get(url, filters)
      .done(function (data) {
        container.tasks = data
        container.taskGroups = splitTasksByProcess(data, processes);
      }).always(function () {
        thisObj.setState({loading: false})
        deferred.resolve()
      })

    return deferred.promise()
  }

  getProducts(container) {
    var deferred = $.Deferred();

    $.ajax(window.location.origin + "/ics/products/")
      .done(function (data) {
        container.products = mapifyProcesses(data)
        deferred.resolve();
      })

    return deferred.promise()
  }

  getProcesses(container) {
    var deferred = $.Deferred();

    $.ajax(window.location.origin + "/ics/processes/")
      .done(function (data) {
        container.processes = mapifyProcesses(data)
        deferred.resolve();
      })

    return deferred.promise()
  }

  parseFilters() {

    let state = this.state.activeFilters
    var filters = {ordering : 'process_type__x' }

    if (this.props.inventory) {
    	filters.inventory = true
    } else {
      filters.ordering = "-created_at"
    }

    if (!this.props.inventory) {
      if (state.start && state.start.length > 0) {
        filters.start = state.start
      }
      if (state.end && state.end.length > 0) {
        filters.end = state.end
      }
    }

    if (state.processes && state.processes.length > 0) {
      filters.processes = state.processes.map(function (x) {
        return x.value
      }).join(",")
    }

    if (state.products && state.products.length > 0)
      filters.products = state.products.map(function (x) {
         return x.value
      }).join(",")

    if (state.label && state.label != "") {
      filters.label = state.label
    }

    return filters
  }

  handleFilter(object, push) {
    let ns = update(this.state, {
      activeFilters: {
        $merge: object
      }
    })

    var thisObj = this
    var newState = {}

    if (object && object.active) {
      this.setState(ns)
    } else {
      this.setState(ns, function () {
        if (push) {
          window.history.pushState(ns.activeFilters, "Scoop @ Bama", 
              window.location.origin + window.location.pathname + "?" + $.param(thisObj.parseFilters(ns.activeFilters)));
        }
        var defs = [this.getTasks(newState, -2, this.props.inventory)]
        $.when.apply(null, defs).done(function() {
          thisObj.setState(newState)
        });
      })
    }


  }

}

// ------––––––––––––––––––––––––––––

function mapifyProcesses(processes) {
  var p = {}
  processes.map(function (obj, i) {
    p[obj.id] = obj
  });
  return p
}

function splitTasksByProcess(tasks, processes) {
  var taskGroups = {}

  tasks.map(function (task, i) {

    let found = getSemanticTaskGroup(task, processes)

    if (!taskGroups[found])
      taskGroups[found] = {count: 0, tasks: []};

    taskGroups[found].tasks.push(task);
    taskGroups[found].count += task.items.length
  });

  return taskGroups;
}

function getSemanticTaskGroup(task, processes) {
  var found = -1

    // if its a label
    if (task.process_type.id == 1 && task.custom_display && processes) {

      // get the code from here
      var label = task.custom_display.split(/[\s-_]+/)
      if (label.length > 0) {
        label = label[0]
      }

      // now check if the code matches anything
      Object.keys(processes).map(function (p) {
        if (processes[p].code.toUpperCase() == label.toUpperCase())
          found = p
      })
    }

    if (found == -1) {
      found = task.process_type.id
    }

    return found
}

