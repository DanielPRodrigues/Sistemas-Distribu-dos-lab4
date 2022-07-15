from unittest.main import main
import rpyc
from rpyc.utils.server import ThreadedServer
from sys import exit

topografia = []
id = int(input("Informe o ID referente a sua aplicação (1 ate n)"))
porta = 5000 + id 

#Lendo o arquivo de topografia
with open('topografia.txt') as arquivo:
    topografia = arquivo.readlines()

topografia = topografia[id-1]
topografia = topografia.replace("\n","")
vizinhos = topografia.split(" ")
print (vizinhos)

#variáveis auxiliares
probe = False
paias = 0
retorno = []
filhos = []
tipo = 0
wait = True
inicial = False
retornoff = 0

class ProbEcho(rpyc.Service):
    
    def on_connect(self,conn):
        print("Conexão iniciada")
    
    def on_disconnect(self,conn):
        print("Conexão encerrada") 

    #Reiniciando os valores para multiplas eleições
    def exposed_reset(self):
        global probe
        global paias
        global filhos
        global retorno
        global tipo
        global wait
        global inicial
        global retornoff
        global topografia
        global vizinhos
        with open('topografia.txt') as arquivo:
            topografia = arquivo.readlines()
        topografia = topografia[id-1]
        topografia = topografia.replace("\n","")
        vizinhos = topografia.split(" ")
        probe = False
        paias = 0
        del retorno[:]
        del filhos [:]
        tipo = 0
        inicial = False
        retornoff = 0
    
    def exposed_election(self,tipo):
        global vizinhos
        global retorno
        global wait
        global inicial
        global id
        global filhos
        global retornoff
        global probe
        wait = True
        print("Votação iniciada {}".format(id))
        print(paias)
        #Checando se o node é o que foi iniciado pelo programa auxiliar ou por um probe
        # se no pai for diferente de 0, ele foi iniciado por um probe, logo ele retira seu pai da sua lista de vizinhos
        if paias != 0:
            try:
                print("Removedo pai {}".format(paias))
                vizinhos.remove(str(paias))
                print("Testando remove\n")
                print(vizinhos)
            except:
                pass
        else:
            print("Processo {} e o inicial".format(id))
            inicial = True
            probe = True
        
        print("vizinhos de {}:{}".format(id,vizinhos))
        
        #Fazendo probe para todos os vizinhos
        for vizinho in vizinhos:
            conn = rpyc.connect('localhost', 5000+int(vizinho))
            retornin = conn.root.exposed_probe(id)
            conn.close()
            #Se o retorno da função nao foi ack, manda o vizinho iniciar sua propria eleição
            if retornin != 'ACK':
                filhos.append(int(vizinho))
                print("filhos:{}".format(filhos))
                print("mandando {} iniciar sua eleição".format(int(vizinho)))
                conn = rpyc.connect('localhost', 5000+int(vizinho))
                conn.root.exposed_election(tipo)
                conn.close()                                
        print("Acabaram os vizinho do {}".format(id))
        #Caso aonde o ack é igual ao numero de vizinhos, ou seja, esse node ja pode iniciar seu processo de echo
        print("Filhos do processo {}:{}".format(id,filhos))             
        while wait:
            #Aguardando os filhos encerrarem seus calculos parciais, para encontrar o seu proprio resultado parcial e enviar ao no pai
            if filhos == [] and not inicial:
                wait = False
                retorno.append(id)
                if tipo == 'M':
                    retornoff = max(retorno)
                elif tipo == 'm':
                    retornoff = min(retorno)
                conn = rpyc.connect('localhost',5000 + paias)
                conn.root.exposed_echo(id,retornoff)
                conn.close()
                print("Retorno enviado pelo processo {} foi {}".format(id,retornoff))
                self.exposed_reset()
            #Processo final, que calculara o resultado real da eleição
            elif filhos == [] and inicial:
                print("Pra fechar..")
                print("retorno final: {}".format(retorno))
                #Finalmente encontrando o lider, utilizando seu proprio id mais os resultados parciais de seus filhos
                retorno.append(id)
                if tipo == 'M':
                    return max(retorno)
                elif tipo == 'm':
                    return min(retorno)
        wait = True
            
    def exposed_probe(self,id_pai):
        global probe
        global paias
        #Se já tiver recebido probe antes
        if probe:
            return 'ACK'
        else:
            probe = True
            paias = id_pai
            print("Probe recebido com sucesso, o pai do processo {} é: {}".format(id,paias))
            return 'sucesso'
        
        
    def exposed_echo(self,id_filho,retorno_filho):
        print("enviando Echo")
        global retorno
        global filhos
        #Adicionando o retorno global ao retorno doseu filho
        retorno.append(retorno_filho)
        #Removendo o filho
        try:
            filhos.remove(id_filho)
        except:
            print("Falha ao remover {} de {} na função echo dos cria".format(id_filho,filhos))
        print(retorno)
        print("Echo enviado")
       
            
#Iniciando o servidor
if __name__ == "__main__":
    server = ThreadedServer(ProbEcho,port = porta)
    server.start()
