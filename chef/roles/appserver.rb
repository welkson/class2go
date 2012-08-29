name "appserver"
description "Class2Go appserver node"

override_attributes({
    "class2go-bitnami-django" => {
            "django-app" => "main"
            }
})


# For now not doing an update/upgrade before everything else since it
# can cause mysterious problems and takes so darn long.  have to do it 
# on the util machines though

run_list(
#   "recipe[chef-client]",
#   "recipe[class2go-update]",
    "recipe[gdata]",
    "recipe[class2go-base]",
    "recipe[class2go-python]",
    "recipe[class2go-bitnami-django]",
    "recipe[class2go-deploy]",
    "recipe[class2go-logging]",
    "recipe[class2go-database.py]",
    "recipe[class2go-collectstatic]",
    "recipe[class2go-bitnami-apache-restart]"
)
