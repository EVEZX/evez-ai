class Router:
    ROUTES={
        'code':'EVEZ-Code',
        'reasoning':'EVEZ-Logic',
        'prediction':'EVEZ-Temporal',
        'memory':'EVEZ-Vector'
    }
    def route(self,task):
        task=task.lower()
        for k,v in self.ROUTES.items():
            if k in task:
                return v
        return 'EVEZ-Core'
