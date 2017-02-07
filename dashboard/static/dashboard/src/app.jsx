import React from 'react';
import ReactDOM from 'react-dom';
import { Navbar} from './Layout.jsx'
import Tasks from './Tasks.jsx'
import FactoryMap from './FactoryMap.jsx'
import LabelPrinter from './LabelPrinter.jsx'

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
    this.state = {
      active: -1,
    };

  }

  componentDidMount() {
    var str = window.location.href
    if (str.lastIndexOf("/") == str.length - 1) {
      str = str.substr(0, str.length-1)
    }
    var pieces = str.split("/")
    let piece = pieces[pieces.length - 1]
    if (piece == "" || piece == "dashboard")
      this.setState({active: 1})
    if (piece == "inventory")
      this.setState({active: 2})
    if (piece == "labels")
      this.setState({active: 3})
    if (piece == "settings")
      this.setState({active: 4})
  }

  render() {

    var obj = <Tasks inventory={(this.state.active==2)} />

    if (this.state.active == 3) {
      obj = <LabelPrinter />
    }

    if (this.state.active == 4) {
      obj = false
    }

    return (
      <div className="parent">
        <div className="content-area">

          <Navbar 
            options={["Activity Log", "Inventory", "Labels", "Settings"]}
            links={["", "inventory", "labels", "settings"]} 
            active={this.state.active} 
            onNav={ (x) => this.setState({active: x}) }
          />

          {obj}

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

}

ReactDOM.render(
  <Main />,
  document.getElementById('root')
);