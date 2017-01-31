import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import {Table, TableList} from './Tables.jsx';
import { Filters } from './Inputs.jsx';
import { Navbar, ContentDescriptor } from './Layout.jsx'

function SectionHeader(props) {
  return (
    <div className="section-header">
      <i className="material-icons">{props.icon}</i>
      <h1>{props.title}</h1>
    </div>
  );
}

class Main extends React.Component {
  constructor() {
    super();
    this.handleFilter = this.handleFilter.bind(this);
    this.state = {
      taskGroups: {},
      processes: {},
      products: {},
      count: 0,
      total: 0,
      active: 1,
      previous: null,
      next: null,
      startIndex: 0,
      currentPage: 1
    };

  }

  render() {
    return (
      <div className="parent">
        <div className="content-area">
          <Navbar options={["Activity Log", "Inventory", "Settings"]} active={this.state.active} onNav={ (x) => this.setState({active: x}) }/>

          <div className="content">
            <ContentDescriptor count={this.state.count} total={this.state.total} previous={this.state.previous} next={this.state.next} startIndex={this.state.startIndex} onPage = { (x) => this.handlePage(x)}/>
            <TableList taskGroups={this.state.taskGroups} processes={this.state.processes}/>
          </div>

          <div className="sidebar">
              <Filters processes={this.state.processes} products={this.state.products} onFilter={(state) => this.handleFilter(state)}/>
          </div>

        </div>
      </div>
    );
  }

  handleNav(x) {
    if (x > 1) {
      return
    }

    this.setState({active: x})
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
    var newState = { taskGroups: [], processes: [], products: [] };

    var defs = []

    defs.push(this.getProcesses(newState));
    defs.push(this.getProducts(newState));

    var component = this

    $.when.apply(null, defs).done(function() {

      component.setState(newState, function () {
        var d2 = []
        d2.push(component.getTasks(newState, activeFilters));
        $.when.apply(null, d2).done(function () {
          component.setState(newState)
        })
      })
    })
  }

  getTasks(container, filters, page) {
    var deferred = $.Deferred();

    var url = window.location.origin + "/ics/tasks/"

    if (page) {
      url += "?page=" + page
    }

    var processes = this.state.processes
    if (!processes) 
      processes = container.processes

    console.log("PROCESSES: ") 
    console.log(this.state.processes)

    $.get(url, filters)
      .done(function (data) {
        container.count = data.results.length
        container.total = data.count
        container.next = data.next ? data.next.match(/page=(\d*)/)[1] : null
        container.previous = data.previous && data.previous.match(/page=(\d*)/) ? data.previous.match(/page=(\d*)/)[1] : null
        container.startIndex = 0
        container.currentPage = 1
        container.taskGroups = splitTasksByProcess(data.results, processes);
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

    if (this.state.active == 1) {
      filters.inventory = "True"
    }

    if (!state.inventory && state.start && state.start.length > 0 && state.end && state.end.length > 0) {
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

function mapifyProcesses(processes) {
  var p = {}
  processes.map(function (obj, i) {
    p[obj.id] = obj
  });
  return p
}

function splitTasksByProcess(tasks, processes) {
  var taskGroups = {}

  console.log("SPLITTING TASKS")

  tasks.map(function (task, i) {

    var found = -1

    // if its a label
    if (task.process_type == 1 && task.custom_display && processes) {

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
      found = task.process_type
    }

    if (!taskGroups[found])
      taskGroups[found] = [];

    taskGroups[found].push(task);
  });

  return taskGroups;
}

ReactDOM.render(
  <Main />,
  document.getElementById('root')
);