import React from "react";

import { Layout } from 'antd';

const { Header, Footer, Sider, Content } = Layout;

import "./CSS/BasicPage.css";

class BasicPage extends React.Component{
    render() {
        return(
            <Layout>
                <Header style={{height: "8vh"}}>{this.props.navbar}</Header>
                <Content style={{height: "82vh"}}>{this.props.element}</Content>
                <Footer style={{height: "10vh"}}>Footer</Footer>
            </Layout>
        )
    }

}

export default BasicPage;