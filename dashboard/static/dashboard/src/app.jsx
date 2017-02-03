import React from 'react';
import ReactDOM from 'react-dom';
import { Navbar} from './Layout.jsx'
import Tasks from './Tasks.jsx'
import FactoryMap from './FactoryMap.jsx'

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
      active: 2,
    };

  }

  render() {

    var obj = <Tasks inventory={this.state.active} />

    if (this.state.active == 2) {
      obj = <FactoryMap />
    }

    return (
      <div className="parent">
        <div className="content-area">

          <Navbar 
            options={["Activity Log", "Inventory", "Settings"]} 
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