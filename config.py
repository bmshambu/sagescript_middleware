class AppConfig:
    def __init__(self):
        #self.api_key = "AIzaSyCBINU8A2euMr6ebSrhfv3ma2XAytvU19g"
        self.api_key = "AIzaSyAqE9KzHW_fw-e0qhcJqio0gaIhMPV_a3I"
        self.base_url = ''
        self.version = ''
        #self.model_name = "gemini-3-flash"
        self.model_name ="gemini-2.5-flash"
        self.database_url ="postgresql://sage_script_sql_user:LOvz5raotz1inmrMnJ1L6hVgofjwVI9B@dpg-d5s6qljlr7ts738nu0i0-a.oregon-postgres.render.com/sage_script_sql"
        self.lang_settings={
    "Python": { "extension": ".py", "framework": "unittest or pytest" },
    "JavaScript": { "extension": ".test.js", "framework": "Jest" },
    "TypeScript": { "extension": ".test.ts", "framework": "Jest or Mocha" },
    "Java": { "extension": "Test.java", "framework": "JUnit" }
}
        
