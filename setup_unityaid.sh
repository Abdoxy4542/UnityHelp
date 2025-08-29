mkdir -p {
    config,
    apps/{accounts,sites,reports,assessments,alerts,integrations,dashboard,mcp_servers},
    static/{css,js,images},
    media/{uploads,temp},
    templates/{base,dashboard,mobile},
    docs,
    requirements,
    scripts,
    tests,
    locale/{ar,en},
    logs,
    deployment/{docker,k8s,nginx}
}
