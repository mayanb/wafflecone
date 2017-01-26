import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import {Table, TableList} from './Tables.jsx';
import { Filters } from './Inputs.jsx';
import { Navbar } from './Layout.jsx'

//<TableList taskGroups={this.state.taskGroups} processes={this.state.processes}/>
//<Filters processes={this.state.processes} products={this.state.products} onFilter={(state) => this.handleFilter(state)} disabled={this.state.filterDisabled}/>

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
      filterDisabled: false
    };

  }

  render() {
    return (
      <div className="parent">
        <div className="content-area">
          <Navbar title="Task Log" title2="Inventory"/>
          <div className="content">
            <TableList taskGroups={this.state.taskGroups} processes={this.state.processes}/>
          </div>
        </div>
        <div className="sidebar">
          <Navbar title="dsa"/>
          <div className="content">
            <Filters processes={this.state.processes} products={this.state.products} onFilter={(state) => this.handleFilter(state)} disabled={this.state.filterDisabled}/>
          </div>
        </div>

      </div>
    );
  }

  componentDidMount() {
    var newState = { taskGroups: [], processes: [], products: [] };

    var defs = [];

    defs.push(this.getProcesses(newState));
    defs.push(this.getProducts(newState));
    defs.push(this.getTasks(newState, ""));

    var component = this

    $.when.apply(null, defs).done(function() {
      component.setState(newState)
    });
  }

  getTasks(container, querystring) {
    var deferred = $.Deferred();

    $.ajax(window.location.origin + "/ics/tasks/?" + querystring)
      .done(function (data) {
        container.taskGroups = splitTasksByProcess(data.results);
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

  handleFilter(state) {
    this.setState({filterDisabled: true})

    var filters = {}

    if (state.inventory)
      filters.inventory = "True";

    if (!state.inventory && state.start && state.start.length > 0 && state.end && state.end.length > 0) {
      filters.start = state.start
      filters.end = state.end
    }

    if (state.processes.length > 0)
      filters.processes = state.processes.map(function (x) {
        return x.value
      }).join(",")

    if (state.products.length > 0)
      filters.products = state.products.map(function (x) {
        return x.value
      }).join(",")

    if (state.parent && state.parent != "") {
      filters.parent = state.parent
    }

    if (state.child && state.child != "") {
      filters.child = state.child
    }

    var thisObj = this

     $.get(window.location.origin + "/ics/tasks/", filters)
      .done(function (data) {
        var taskGroups = splitTasksByProcess(data.results);
        thisObj.setState({taskGroups : taskGroups})
      }).always(function () {
        thisObj.setState({filterDisabled: false})
      })

  }


}

function mapifyProcesses(processes) {
  var p = {}
  processes.map(function (obj, i) {
    p[obj.id] = obj
  });
  return p
}

function splitTasksByProcess(tasks) {
  var taskGroups = {}
  tasks.map(function (task, i) {
    if (!taskGroups[task.process_type])
      taskGroups[task.process_type] = [];

    taskGroups[task.process_type].push(task);
  });
  return taskGroups;
}

ReactDOM.render(
  <Main />,
  document.getElementById('root')
);