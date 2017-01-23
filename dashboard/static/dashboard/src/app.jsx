import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import {Table, TableList} from './Tables.jsx';
import { Filters } from './Inputs.jsx';
import { Navbar } from './Layout.jsx'


// <Multiselect options={this.state.products} placeholder="Filter by product..."/>

class Main extends React.Component {
  constructor() {
    super();

    this.state = {
      taskGroups: {},
      products: {},
    };

  }

  render() {
    return (
      <div className="parent">
        <Navbar />
        <div className="content">
          <div className="container">
            <Filters processes={this.state.processes} products={this.state.products}/>
            <TableList taskGroups={this.state.taskGroups} processes={this.state.processes}/>
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
    defs.push(this.getTasks(newState));

    var component = this

    $.when.apply(null, defs).done(function() {
      component.setState(newState)
    });
  }

  getTasks(container) {
    var deferred = $.Deferred();

    $.ajax(window.location.origin + "/ics/tasks/")
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