<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:key name="classkey" match="testcase" use="@classname"/>
    <xsl:output method="html"/>
    <xsl:template match="/">
        <xsl:text disable-output-escaping="yes"><![CDATA[<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">]]></xsl:text>
        <html>
            <head>
                <title>
                    Everest Selenium Test Results
                </title>
                <style>
                    body {
                        color: #333333;
                        font-family: Tahoma, Geneva, sans-serif;
                        font-size: 11px
                    }

                    .container {
                        position:fixed;
                        padding: 10px;
                        margin-left: 7px;
                        background-color: rgb(255,230,160);
                        border-color: rgb(150,150,150);
                        border-style:solid;
                        border-width:2px;
                    }

                    .testcases {
                       border-style:solid;
                       border-width:0px;
                       border-color:#333333;
                       padding:5px;
                     }

                    .filters {
                        margin: 10px 0 0 0;
                     }

                    .failed {
                        display:block;
                        background-color: rgb(255, 240, 240);
                        padding: 10px;
                        margin: 2px
                    }

                    .failed a {
                        color: red;
                        font-weight: bold;
                    }

                    .passed {
                        display: block;
                        background-color: rgb(225, 255, 225);
                        padding: 10px;
                        margin: 2px
                    }

                    .passed a {
                        color: green;
                        font-weight: bold;
                    }

                    .error-message {
                       border-style:solid;
                       border-width:1px;
                       border-color:rgb(225, 100, 100);
                       padding: 5px;
                       display: none
                    }
                    .clickable:hover {
                        cursor: pointer;
                        cursor: hand;
                    }
                    .hide_error {
                        display: none;
                    }
                </style>
                <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.7/jquery.min.js"/>
                <script type="text/javascript">
                    $(document).ready(function() {
                        $('.toggle_error').click(function() {
                            $(this).next().toggle('fast');
                            $(this).children('.hide_error').toggle();
                            $(this).children('.show_error').toggle();
                        })

                    });

                    function show_all_errors() {
                        $('.error-message').show();
                        $('.hide_error').show();
                        $('.show_error').hide();
                    }
                    function hide_all_errors() {
                        $('.error-message').hide();
                        $('.hide_error').hide();
                        $('.show_error').show();
                    }

                    function show_tests(type) {
                        switch(type) {
                            case "passed":
                                $('.passed').show();
                                $('.failed').hide();
                                break;
                            case "failed":
                                $('.passed').hide();
                                $('.failed').show();
                                break;
                            case "all":
                                $('.passed').show();
                                $('.failed').show();
                                break;
                        }
                    }
                </script>
            </head>
            <body>
                <xsl:apply-templates>
                    <xsl:sort select="testcase/@classname"/>
                </xsl:apply-templates>
            </body>
        </html>

    </xsl:template>
    <xsl:template match="testsuite">

        <div class="container">
            Tests run: <b><xsl:value-of select="@tests"/></b>
            Failures: <b><xsl:value-of select="@failures"/></b>,
            Skipped: <b><xsl:value-of select="@skips"/></b>,
            Errors: <b><xsl:value-of select="@errors"/></b> |
            <span class="clickable" onclick="show_all_errors();"><b>[+]</b> Show all errors, </span>
            <span class="clickable" onclick="hide_all_errors();"> <b>[-]</b> Hide all errors</span>
            <form>
                <input type="radio" onclick="show_tests('passed');" name="filter" value="passed"/>Passed
                <input type="radio" onclick="show_tests('failed');" name="filter" value="failed"/>Failed
                <input type="radio" onclick="show_tests('all');" name="filter" value="all"/>All
            </form>
        </div>
        <div style="height:60px"/>

        <div class="testcases">
        <xsl:for-each select="testcase">
            <xsl:choose>
                <xsl:when test="not(failure)">
                    <div class="passed">
                        <span style="display: inline-block; width:200px"><b><xsl:value-of select="@name"/></b></span>
                        <span style="display: inline-block; width:600px"><xsl:value-of select="@classname"/></span>
                        <span><b>Running Time:</b> <xsl:value-of select="@time"/></span>
                   </div>
                </xsl:when>
                <xsl:otherwise>
                    <div class="failed">
                        <span style="display: inline-block; width:200px"><b><xsl:value-of select="@name"/></b></span>
                        <span style="display: inline-block; width:600px"><xsl:value-of select="@classname"/></span>
                        <span><b>Running Time:</b> <xsl:value-of select="@time"/></span>
                        <div style="padding-top: 5px">
                        <xsl:for-each select="failure">
                            <span class="toggle_error clickable">
                                <div class="hide_error"><b>[-]</b> hide error</div>
                                <div class="show_error"><b>[+]</b> show error</div>
                            </span>
                            <div class="error-message">
                                <pre><xsl:value-of select="text()"/></pre>
			                    <xsl:value-of select="error"/>
                            </div>
                        </xsl:for-each>
                        </div>
                    </div>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
        </div>

    </xsl:template>

</xsl:stylesheet>