import React from 'react';
import ReactDOM from 'react-dom';
import {message, Tag, Button, Menu, Dropdown, Icon, Table, Divider, Card, Layout} from 'antd';
import './components/index.css';
import registerServiceWorker from './components/registerServiceWorker';
import ReactTable from "react-table";
import "react-table/react-table.css";
import axios from 'axios';
import matchSorter from 'match-sorter';
import 'antd/dist/antd.css';  // or 'antd/dist/antd.less'
import 'react-table/react-table.css'
import {DataTable} from 'antd-data-table'
import ReactChartkick, {LineChart, PieChart} from 'react-chartkick'
import Chart from 'chart.js'
import {Line} from 'react-chartjs-2';
import Plot from 'react-plotly.js';
import {InitialSpeciesList, SearchAndExecute, CommonPropertiesList, SearchMain, CurveMatchingResult, ExperimentExecutionsCMDetails} from "./components/Search"
import {ExperimentTableV2} from "./components/Db"
import {WrappedCommonPropertiesForm,WrappedDataForm} from "./components/Input"


const { Header, Content, Footer } = Layout;


ReactChartkick.addAdapter(Chart)

String.prototype.format = function () {
    let a = this;
    for (let k in arguments) {
        a = a.replace("{" + k + "}", arguments[k])
    }
    return a
};


class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            current : 'experiments'
        }
    }

    handleMenuClick = (e) => {
        console.log('click ', e);
        this.setState({
            current: e.key,
        });
    };

    render() {
        const current = this.state.current;
        const currentMapping = {"experiments" : <ExperimentTableV2/>, "searchandexecute" : <SearchAndExecute/>, "input": <WrappedDataForm/>, "input-form": <WrappedCommonPropertiesForm/>}

        return (
            <Layout className="layout">
 <Header>
                    {/*<div className="logo">SciExpeM-SMOKE</div>*/}
                    <Menu
                        theme="dark"
                        mode="horizontal"
                        defaultSelectedKeys={[this.state.current]}
                        onClick={this.handleMenuClick}

                        style={{lineHeight: '64px'}}
                    >
                        <Menu.Item key="main"><b>SciExpeM-SMOKE</b></Menu.Item>
        <Menu.SubMenu title={<span className="submenu-title-wrapper"><Icon type="upload" />Insert experiments</span>}>

            <Menu.Item key="input" >Insert using input file</Menu.Item>

            <Menu.Item key="input-form">Insert using form</Menu.Item>


        </Menu.SubMenu>
                        <Menu.Item key="experiments"><Icon type="database"/>Experimental database</Menu.Item>
                        <Menu.Item key="searchandexecute"><Icon type="line-chart"  />Search & Execute</Menu.Item>
                        <Menu.Item key="about"><Icon type="info-circle"  />About</Menu.Item>
                    </Menu>
                </Header>
                <Content style={{padding: '0 50px'}}>
                    <div style={{background: '#fff', padding: 24, minHeight: 280}}>
                        {currentMapping[current]}

                    </div>
                </Content>
                <Footer style={{textAlign: 'center'}}>
                    ©2018 Politecnico di Milano
                </Footer>
            </Layout>)
    }
}


ReactDOM.render(<div><App/></div>, document.getElementById("root"));

