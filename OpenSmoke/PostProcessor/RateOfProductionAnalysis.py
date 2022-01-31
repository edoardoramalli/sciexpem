"""
nr number of reactions
nos number of species
nur coefficient reactants
nup coefficients products
"""
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd


class RateOfProductionAnalysis:
	
    '''
    This Class performs a Rate Of Production Analysis
    '''

    def __init__(self, outxmlpath, NumberOfSpecies, NumberOfReactions, nur, nup, reactions_lines, nomi):

          
        # Read data from xml file
               
        tree_out = ET.parse(outxmlpath)
        root_out = tree_out.getroot()                                                     
        
        massfractions_element = root_out.find('mass-fractions')
        profiles = root_out.find('profiles')
        profiles = profiles.text.split()
        profileSize = root_out.find('profiles-size')
        profileSize = profileSize.text.split()
        NumberOfRows = int(profileSize[0])
        NumberOfColumns = int(profileSize[1])
        profiles = np.reshape(profiles, (NumberOfRows, int(len(profiles) / NumberOfRows)))
        profiles = profiles.astype(np.float)
    
        time = profiles[:,0]
        
        gas_reaction_rates = root_out.find('reaction-rates') 
        gas_reaction_rates = np.float64(gas_reaction_rates.text.split()) # questo non è un vettore ma bensì una matrice di dimensione
                                                                         # NumberOfReactions x altra dimensione
                                                                         # altra dimensione la trovo in profile size dove primo numero
                                                                         # numero di righe e secondo numero numero di colonne

        fullMatrixReactionRates = np.reshape(gas_reaction_rates,(NumberOfRows, NumberOfReactions))
        
        # tmp = fullMatrixReactionRates[0,:]
        # df = pd.DataFrame(tmp)
        # df.to_excel(excel_writer = "fullMatrix_New2.xlsx")

        # exit()
        gas_formation_rates = root_out.find('formation-rates') 
        gas_formation_rates = np.float64(gas_formation_rates.text.split())
         # fullMatrixFormationRates = np.reshape(gas_formation_rates,(NumberOfRows, NumberOfReactions))

        Type = 'Global'
        selectedRates = []
        
        if Type == 'Global':
            """
            Description: TODO
            """
            # for i in range(NumberOfReactions):
                # tmp = max(fullMatrixReactionRates[:,i], key=abs)
            tmp = fullMatrixReactionRates[0,:]
            print(NumberOfReactions)
                # tmp = np.trapz(fullMatrixReactionRates[:,i], x = time)
                # ciao = self.trapz(fullMatrixReactionRates[:,i], 0, 4.877112, 234)
                
            selectedRates.append(tmp)
            selectedRates = selectedRates[0]
        elif Type == 'Local':
            """
            TODO
            """
            pass
        elif Type == 'Region':
            """
            TODO
            """
            pass
        else:
            raise ValueError('Available Types of ROPA analysis: Global | Local | Region')

        ContributionInProduction = np.zeros(nur.shape)
        ContributionInConsumption = np.zeros(nup.shape) 
         
        nup = nup.toarray()
        nur = nur.toarray()
        
        # robetta = {'nup': [], 'NumeroReazione': [], 'Reazione': [], 'Specie': [], 'rate': [], 'Contrib': []}
        # for j in range(NumberOfReactions):
        #     for i in range(NumberOfSpecies):
        #         ContributionInProduction[j, i] = nup[j,i] * selectedRates[j]
                # robetta['Contrib'].append(ContributionInProduction[j,i])
                # robetta['NumeroReazione'].append(j)
                # robetta['Specie'].append(nomi[i])
                # robetta['Reazione'].append(reactions_lines[j])
                # robetta['rate'].append(selectedRates[j])
                # robetta['nup'].append(nup[j,i])
        cazz = {'nup': [], 'nur': [],'NumeroReazione': [], 'Reazione': [], 'Specie': [], 'rate': []}
        # exit()

        # for j in range(NumberOfReactions):
        #     for i in range(NumberOfSpecies):
        #         ContributionInConsumption[j, i] = selectedRates[j] # *nur
        #         ContributionInProduction[j, i] = selectedRates[j] # *nup
        for j in range(NumberOfReactions):
            if nur[j,0] != 0 or nup[j,0] != 0:

                cazz['nup'].append(nup[j,0])
                cazz['nur'].append(nur[j,0])
                cazz['NumeroReazione'].append(j)
                cazz['Reazione'].append(reactions_lines[j])
                cazz['Specie'].append(nomi[0])
                cazz['rate'].append(selectedRates[j])
               


        df = pd.DataFrame(cazz)
        df.to_excel(excel_writer = "cazzo.xlsx")
        exit()
        print(ContributionInConsumption)
        self.P = ContributionInProduction
        self.C = ContributionInConsumption




        exit()
        # for j in range(NumberOfReactions):
        #     if nur[j,0] != 0:
        #         cazz['nup'].append(nup[j,0])
        #         cazz['nur'].append(nur[j,0])
        #         cazz['NumeroReazione'].append(j)
        #         cazz['Reazione'].append(reactions_lines[j])
        #         cazz['Specie'].append(nomi[0])
        #         cazz['rate'].append(selectedRates[j])
        #         cazz['Contrib'].append(ContributionInConsumption[j,0])

        # df = pd.DataFrame(cazz)
        # df.to_excel(excel_writer = "cazz.xlsx")
        # exit()
        # roba = {'reazione': [], 'rate': [],'nup': [], 'nur': [], 'Contrib': []}
        # for j in range(NumberOfReactions):
        #     if nup[j,0] != 0 or nur[j, 0] != 0:
        #         roba['Contrib'].append(ContributionInConsumption[j,0])
        #         roba['reazione'].append(reactions_lines[j])
        #         roba['rate'].append(selectedRates[j])
        #         roba['nup'].append(nup[j,0])
        #         roba['nur'].append(nur[j,0])

        # df = pd.DataFrame(roba)
        # # df['Coefficients'] = abs(df['rate'])

        # # df = df.sort_values(by=['Coefficients'], ascending=False)
        # df.reset_index(inplace=True)
        # df.to_excel(excel_writer = "integrate.xlsx")
        # exit()

        # for i in range(NumberOfSpecies):
        #     for j in range(NumberOfReactions):
                    
        #         Production_Rate[j,i] = max(nup[j,i]-nur[j,i], 0) * selectedRates[j]
        #             # if Production_Rate[j,i] < 0:
        #             #     print('Prod: ',i,j,Production_Rate[j,i],nup[j,i],nur[j,i],selectedRates[j])
        #         Consumption_Rate[j,i] = min(nup[j,i]-nur[j,i], 0) * selectedRates[j]
        #             # if Consumption_Rate[j,i] > 0:
        #             #     print('Cons: ',i,j,Consumption_Rate[j,i],nup[j,i],nur[j,i],gas_reaction_rates[j])
            
        # for i in range(NumberOfSpecies):
        #     for j in range(NumberOfReactions):

        # # Scambio negative in Production in Consumption e positive in consumption in production
        
        # # print(Consumption_Rate.shape)
        
        tmp_prod = {'j': [], 'i': [], 'Prod': []}
        tmp_cons = {'j': [], 'i': [], 'Cons': []}
        
        for i in range(NumberOfSpecies):
            for j in range(NumberOfReactions):
                if ContributionInProduction[j,i] < 0.:
                    tmp_prod['j'].append(j)
                    tmp_prod['i'].append(i)
                    tmp_prod['Prod'].append(ContributionInProduction[j,i])
                if ContributionInConsumption[j,i] < 0.:
                    tmp_cons['j'].append(j)
                    tmp_cons['i'].append(i)
                    tmp_cons['Cons'].append(ContributionInConsumption[j,i])

        if tmp_prod['j'] != []:
            for k in range(len(tmp_prod['i'])):
                reaz = tmp_prod['j'][k]
                spec = tmp_prod['i'][k]
                rate = tmp_prod['Prod'][k]

                #errore
                ContributionInConsumption[reaz,spec] = rate
                ContributionInProduction[reaz,spec] = 0

        if tmp_cons['j'] != []:
            for k in range(len(tmp_cons['i'])):
                reaz = tmp_cons['j'][k]
                spec = tmp_cons['i'][k]
                rate = tmp_cons['Cons'][k]

                #errore
                ContributionInProduction[reaz,spec] = rate
                ContributionInConsumption[reaz,spec] = 0
        
        # roba = {'reazione': [], 'rate': [],'nup': [], 'nur': [], 'Contrib': []}
        # for j in range(NumberOfReactions):
        #     if nup[j,0] != 0 or nur[j, 0] != 0:
        #         roba['Contrib'].append(ContributionInProduction[j,0])
        #         roba['reazione'].append(reactions_lines[j])
        #         roba['rate'].append(selectedRates[j])
        #         roba['nup'].append(nup[j,0])
        #         roba['nur'].append(nur[j,0])

        # df = pd.DataFrame(roba)
        # df['Coefficients'] = abs(df['rate'])

        # df = df.sort_values(by=['Coefficients'], ascending=False)
        # df.reset_index(inplace=True)
        # df.to_excel(excel_writer = "prod.xlsx")
        # exit()
        Sum_Production = np.zeros(NumberOfSpecies)
        Sum_Consumption = np.zeros(NumberOfSpecies)

        P = np.zeros(nur.shape)
        C = np.zeros(nur.shape)
          
        # # metodo tito
        for i in range(NumberOfSpecies):
            Sum_Production[i] = sum(ContributionInProduction[:,i])
            Sum_Consumption[i] = sum(ContributionInConsumption[:,i])

        # # np.set_printoptions(threshold=np.inf)

        for i in range(NumberOfSpecies):
            for j in range(NumberOfReactions):  

                if Sum_Production[i] == 0: 
                    P[j,i] = 0
                else:
                    P[j,i] = ContributionInProduction[j,i] / Sum_Production[i]

                if Sum_Consumption[i] == 0:
                    C[j,i] = 0
                else:
                    C[j,i] = -(ContributionInConsumption[j,i] / Sum_Consumption[i])
        
        # self.Production_Rate = Production_Rate
        # self.Consumption_Rate = Consumption_Rate
        self.P = P
        self.C = C

    def trapz(self, f, a, b, N=50):
        '''Approximate the integral of f(x) from a to b by the trapezoid rule.

        The trapezoid rule approximates the integral \int_a^b f(x) dx by the sum:
        (dx/2) \sum_{k=1}^N (f(x_k) + f(x_{k-1}))
        where x_k = a + k*dx and dx = (b - a)/N.

        Parameters
        ----------
        f : function
            Vectorized function of a single variable
        a , b : numbers
            Interval of integration [a,b]
        N : integer
            Number of subintervals of [a,b]

        Returns
        -------
        float
            Approximation of the integral of f(x) from a to b using the
            trapezoid rule with N subintervals of equal length.

        Examples
        --------
        >>> trapz(np.sin,0,np.pi/2,1000)
        0.9999997943832332
        '''
        x = np.linspace(a,b,N+1) # N+1 points make N subintervals
        y = f
        y_right = y[1:] # right endpoints
        y_left = y[:-1] # left endpoints
        dx = (b - a)/N
        T = (dx/2) * np.sum(y_right + y_left)
        return T

        
         

