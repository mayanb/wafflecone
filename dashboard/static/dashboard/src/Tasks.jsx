import React from 'react';
import $ from 'jquery';
import TableList from './Tables.jsx';
import { Filters } from './Inputs.jsx';
import { ContentDescriptor } from './Layout.jsx'
import moment from 'moment'
import TaskDialog from './TaskDialog.jsx'

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

      count: 0,
      total: 0,

      previous: null,
      next: null,
      startIndex: 0,
      currentPage: 1,

      activeFilters: { inventory: props.inventory, start: moment(new Date()).format("YYYY-MM-DD").toString(), end: moment(new Date()).format("YYYY-MM-DD").toString() }
    };
  }


	render() {

    console.log(this.state.processes)
		if (this.state.processes == {} || this.state.products == {}) {
			return {false};
		}

		return ( 
			<div>
				<div className="content">

          <ContentDescriptor 
            count={this.state.count} 
            total={this.state.total} 
            previous={this.state.previous} 
            next={this.state.next} 
            startIndex={this.state.startIndex} 
            onPage = { (x) => this.handlePage(x)}
          />

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

        </div>

        <div className="sidebar">
            <Filters 
              processes={this.state.processes} 
              products={this.state.products} 
              dates={this.props.inventory==false}
              onFilter={(state) => this.handleFilter(state)}
            />
        </div>
	    </div>
	  )
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
    var defs = [this.getTasks(newState, this.state.activeFilters, x)]

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
      component.setState(newState)
      var d2 = [component.getTasks(newState, component.state.activeFilters)]
      $.when.apply(null, d2).done(function() {
        component.setState(newState)
      });
    })
  }

  getTasks(container, filters, page) {
    var deferred = $.Deferred();

    var url = window.location.origin + "/ics/tasks/"
    if (page) {
      url += "?page=" + page
    }

    filters.ordering = 'process_type__x'

    var processes = this.state.processes
    if (!processes) 
      processes = container.processes

    $.get(url, filters)
      .done(function (data) {
        container.count = data.length
        container.total = data.count
        container.next = data.next ? data.next.match(/page=(\d*)/)[1] : null
        container.previous = data.previous && data.previous.match(/page=(\d*)/) ? data.previous.match(/page=(\d*)/)[1] : null
        container.startIndex = 0
        container.currentPage = 1
        container.taskGroups = splitTasksByProcess(data, processes);
        deferred.resolve();
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

  parseFilters(state) {

    var filters = {}

    if (this.props.inventory) {
    	filters.inventory = true
    }

    if (!this.props.inventory && state.start && state.start.length > 0 && state.end && state.end.length > 0) {
      filters.start = state.start
      filters.end = state.end
    }

    if (state.processes && state.processes.length > 0)
      filters.processes = state.processes.map(function (x) {
        return x.value
      }).join(",")

    if (state.products && state.products.length > 0)
      filters.products = state.products.map(function (x) {
        return x.value
      }).join(",")

    if (state.parent && state.parent != "") {
      filters.parent = state.parent
    }

    if (state.child && state.child != "") {
      filters.child = state.child
    }

    this.setState({activeFilters: filters})
    return filters
  }

  handleFilter(state) {
    var filters = this.parseFilters(state)

    var thisObj = this
    var newState = {}

    var defs = [this.getTasks(newState, filters)]

    $.when.apply(null, defs).done(function() {
      thisObj.setState(newState)
    });
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
      taskGroups[found] = [];

    taskGroups[found].push(task);
  });

  return taskGroups;
}

