import React from 'react';
import $ from 'jquery';
import TableList from './Tables.jsx';
import { Filters } from './Inputs.jsx';
import { ContentDescriptor } from './Layout.jsx'
import moment from 'moment'
import TaskDialog from './TaskDialog.jsx'
import update from 'immutability-helper';

export default class Tasks extends React.Component {
  constructor(props) {
    super(props);
    this.handleFilter = this.handleFilter.bind(this);
    this.handleTaskToggle = this.handleTaskToggle.bind(this);
    this.handleTaskSave = this.handleTaskSave.bind(this);
    this.state = {

    	inventory: props.inventory,
      activeTask: null,

      taskGroups: {},
      processes: {},
      products: {},

      loading: false,
      mounted: false,

      activeFilters: this.props.filters
    };
  }


	render() {
    if (!window.history.state) {
      window.history.replaceState(this.state.activeFilters, "Scoop @ bama", window.location.href);
    }

    let obj = false;
		if (Object.keys(this.state.processes).length === 0 && this.state.processes.constructor === Object) {
		} else {
      obj = 
      <div>
        <div className="content">


          <TaskDialog 
            active={(this.state.activeTask != null)} 
            task={this.state.activeTask}
            onTaskClose={(task) => this.handleTaskToggle(null)} 
            onTaskSave={(newTask) => this.handleTaskSave(newTask)}
          />

          <TableList 
            taskGroups={this.state.taskGroups} 
            processes={this.state.processes}
            inventory={this.props.inventory}
            onTaskClick={(task) => this.handleTaskToggle(task)}
          />

          <div style={{display: this.state.loading?"block":""}} className="loading">
            <div className="spinner"></div>
          </div>

        </div>

        <div className="sidebar">
            <Filters 
              filters = {this.state.activeFilters}
              active = {this.state.activeFilters.active}
              processes={this.state.processes} 
              products={this.state.products} 
              dates={this.props.inventory==false}
              onFilter={(object) => this.handleFilter(object, true)}
            />
        </div>
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

  handleTaskSave(task) {
    handleTaskToggle(null)
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
    var newState = { taskGroups: {}, processes: {}, products: {} };
    var defs = []

    defs.push(this.getProcesses(newState));
    defs.push(this.getProducts(newState));

    var component = this

    $.when.apply(null, defs).done(function() {
      var d2 = [component.getTasks(newState, -1, component.props.inventory)]
      component.setState(newState)
      $.when.apply(null, d2).done(function() {
        newState.mounted = true
        component.setState(newState)
      });
    })
  }

  getTasks(container, page, inventory) {
    var deferred = $.Deferred();

    var url = window.location.origin + "/ics/tasks/"

    let filters = this.parseFilters()

    var processes = this.state.processes
    if (Object.keys(this.state.processes).length === 0 && this.state.processes.constructor === Object)
      processes = container.processes

    this.setState({loading: true})
    let thisObj = this

    $.get(url, filters)
      .done(function (data) {
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
        container.products = data
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
    }

    if (state.active == 1) {

      if (!this.props.inventory) {
        if (state.start && state.start.length > 0) {
          filters.start = state.start
        }
        if (state.end && state.end.length > 0) {
          filters.end = state.end
        }
      }

      if (state.processes && state.processes.length > 0)
        filters.processes = state.processes.map(function (x) {
          return x.value
        }).join(",")

      if (state.products && state.products.length > 0)
        filters.products = state.products.map(function (x) {
          return x.value
        }).join(",")
    }

    else if (state.active == 2) {
      if (state.parent && state.parent.value != "") {
        filters.parent = state.parent.value
      }
    }

    else if (state.active == 3) {
      if (state.child && state.child.value != "") {
        filters.child = state.child.value
      }
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
          window.history.pushState(ns.activeFilters, "Scoop @ Bama", window.location.origin + window.location.pathname + "?" + $.param(ns.activeFilters));
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

    if (!taskGroups[found])
      taskGroups[found] = {count: 0, tasks: []};

    taskGroups[found].tasks.push(task);
    taskGroups[found].count += task.items.length
  });

  return taskGroups;
}

