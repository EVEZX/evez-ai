from evez.core.router import Router

class Orchestrator:
    def __init__(self):
        self.router=Router()

    def process(self,request):
        module=self.router.route(request)
        return {'module':module,'request':request}
