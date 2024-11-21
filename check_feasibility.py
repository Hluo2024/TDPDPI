'''
Author: Hongyuan Luo
Date: 2024-11-20 19:17:20
LastEditTime: 2024-11-21 18:58:18
FilePath: TDPDPI\check_feasibility.py
'''
import math
import os
import pandas as pd

INF = 1e9
EPS = 1e-6

class instance:
    capacity = float("inf")
    demands = []
    pickup = []
    delivery = []
    coordinates = []
    distances = []
    start_depot = -1
    end_depot = -1
    horizon = []
    instance_name = " "
    service_times = []
    time_windows = []
    speed = []
    speed_intevals_number = []
    speed_intevals = []
    
    nb_commodity = -1
    commodity = []
    commodity_diff = [] # yuan/kg
    commodity_life_span = [] # yuan/kg
    compatibility = []

    # read the result
    solution_route = []

    def __init__(self, file_1, file_2, file_3):

        instances_info = pd.read_csv(file_1, nrows=1) # read the first 2 rows
        instances_detail = pd.read_csv(file_1, header=2, parse_dates=True) # read the detail

        instances_info_value = instances_info.values
        instances_detail_value = instances_detail.values

        if instances_detail_value[0][1] == "X_COORD":
            instances_detail = pd.read_csv(file_1, header=3, parse_dates=True) # read detail
            instances_detail_value = instances_detail.values

        
        num_request = int(instances_info_value[0][3])

        self.capacity = int(instances_info_value[0][1])


        customer_number = int(file_2.split(".", 2)[0].split("_", 2)[1]) 
        node_number = int(customer_number + 2)

        # demands
        self.demands = [0]
        for i in range(customer_number):
            if i < customer_number/2:
                self.demands += [int(instances_detail_value[i+1][3])]
            else:
                self.demands += [int(instances_detail_value[i+1+num_request- int(customer_number/2)][3])]
        self.demands += [0]
        
        # pickup, delivery
        self.pickup = [i for i in range(1, int(customer_number/2+1))]
        self.delivery = [i for i in range(int(customer_number/2+1), int(customer_number+1))]

        # coordinates
        self.coordinates = []
        for i in range(customer_number):
            self.coordinates += [[]]
        for i in range(customer_number):
            for j in range(2):
                if i < customer_number/2:
                    self.coordinates[i] += [float(instances_detail_value[i+1][j+1])]
                else:
                    self.coordinates[i] += [float(instances_detail_value[i+1+num_request- int(customer_number/2) ][j+1])]  
        self.coordinates = [[float(instances_detail_value[0][1]), float(instances_detail_value[0][2])]] + self.coordinates  + [[float(instances_detail_value[0][1]), float(instances_detail_value[0][2])]] 

        # distances           
        self.distances = [[0 for i in range(node_number)] for j in range(node_number)]
        for i in range(node_number):
            for j in range(node_number):
                if file_1.split("/", 3)[2].split("_", 2)[0] == "L":
                    self.distances[i][j] = round(3*math.sqrt((self.coordinates[i][0]-self.coordinates[j][0])**2 + (self.coordinates[i][1]-self.coordinates[j][1])**2), 2)
                else:
                    self.distances[i][j] = round(math.sqrt((self.coordinates[i][0]-self.coordinates[j][0])**2 + (self.coordinates[i][1]-self.coordinates[j][1])**2), 2)

        self.start_depot = 0
        self.end_depot = customer_number + 1

        self.horizon = [0.0, float(instances_detail_value[0][5])]
        self.instance_name = file_1.split("/", 3)[2].split(".", 2)[0] + "_TDPDP_"  + str(customer_number) 
        
        # service time
        self.service_times = [0.]
        for i in range(customer_number):
            if i < customer_number/2:
                self.service_times += [float(instances_detail_value[i+1][6])]
            else:
                self.service_times += [float(instances_detail_value[i+1+num_request- int(customer_number/2)][6])]
        self.service_times += [0.]


        # time windows
        self.time_windows = []
        for i in range(customer_number):
            self.time_windows += [[]]
        for i in range(customer_number):
            for j in range(2):
                if i < customer_number/2:
                    self.time_windows[i] += [float(instances_detail_value[i+1][j+4])]
                else:
                    self.time_windows[i] += [float(instances_detail_value[i+1+num_request- int(customer_number/2) ][j+4])]  
        self.time_windows = [[float(instances_detail_value[0][4]), float(instances_detail_value[0][5])]] + self.time_windows + [[float(instances_detail_value[0][4]), float(instances_detail_value[0][5])]] 

        # speed time intevals
        if file_1.split("/", 3)[2].split("_", 2)[0] == "L":
            self.speed = [1.8, 1.3, 1.8, 1.3, 1.8, 1.3]  #  3 days time-dependent speed
            self.speed_intevals_number = 6
            self.speed_intevals = []
            for i in range(self.speed_intevals_number):
                self.speed_intevals += [[i*self.horizon[1]/self.speed_intevals_number, (i+1)*self.horizon[1]/self.speed_intevals_number]]  
        elif file_1.split("/", 3)[2].split("_", 2)[0] == "N":
            self.speed = [1.3, 0.7, 1.3, 0.7, 1.3]  # 1 day time-dependent speed 
            self.speed_intevals_number = 5
            ratio = [0, 7, 9, 17, 19, 24] 
            self.speed_intevals = []
            for i in range(self.speed_intevals_number):
                self.speed_intevals += [[ratio[i]*self.horizon[1]/24, ratio[i+1]*self.horizon[1]/24]]  
        elif file_1.split("/", 3)[2].split("_", 2)[0] == "S":
            self.speed = [0.8, 0.7, 1, 1.2]  # 4 hours time-dependent speed 
            self.speed_intevals_number = 4
            self.speed_intevals = []
            for i in range(self.speed_intevals_number):
                self.speed_intevals += [[i*self.horizon[1]/self.speed_intevals_number, (i+1)*self.horizon[1]/self.speed_intevals_number]]  


        # commodity information
        commodity_info = pd.read_csv(file_2, header=None) 
        commodity_detail = pd.read_csv(file_3, header=None) 
    
        commodity_info_value = commodity_info.values
        commodity_detail_value = commodity_detail.values

        self.nb_commodity =  int(commodity_detail_value[0][1])

        # commodity name index
        self.commodity = []
        for i in range(int(customer_number/2)):
            self.commodity += [int(commodity_info_value[i])]
        self.commodity = [0] + self.commodity + self.commodity + [0]

        self.commodity_diff = [] 
        self.commodity_life_span = [] 
        for i in range( self.nb_commodity ):
            if i < 6:
                self.commodity_diff  += [float(commodity_detail_value[i+3][2])]
                self.commodity_life_span += [int(commodity_detail_value[i+3][3])]
            else:
                self.commodity_diff  += [0]
                self.commodity_life_span += [0]       


        self.compatibility = []
        for i in range( self.nb_commodity ):
            self.compatibility += [[]]
        for i in range( self.nb_commodity ):
            for j in range( self.nb_commodity ):
                self.compatibility[i] += [int(commodity_detail_value[i+22][j+1])]

    # time_d is the departure time, from i to j
    def get_travel_time(self, i, j, time_d):
        # intinal remaining distance and intinal now
        distance = self.distances[i][j]
        now = time_d
        for k in range((len(self.speed_intevals))):
            # Determine whether the remaining distance is 0
            if abs(distance) < EPS: 
                break
            # find the first time > departure time
            if self.speed_intevals[k][1] + EPS < time_d:
                continue
            # calculate the time in speed_interval k and update the now
            temp_time = min(distance/self.speed[k], self.speed_intevals[k][1] - max(self.speed_intevals[k][0], now))
            now += temp_time
            # Remaining distance
            distance -= temp_time * self.speed[k]

        if distance > EPS:
            # Cannot reach j within the time interval
            return INF
        return now - time_d

    
    def read_solution(self, path_solution, algorithm):
        self.solution_route = []
        if os.path.isfile(path_solution + self.instance_name + "_" + algorithm + ".txt"):
            with open(path_solution + self.instance_name + "_" + algorithm + ".txt", 'r') as f:   
                variable_list = f.readlines()

            check_length = 0
            for line in variable_list:
                stripped_line = line.strip()
                if stripped_line.startswith("Route"):
                    start = stripped_line.find("[")
                    end = stripped_line.find("]")
                    if start != -1 and end != -1:
                        # Extract and convert to list
                        route = stripped_line[start + 1:end].split(", ")
                        # Convert to integer
                        route = [int(x) for x in route]
                        self.solution_route.append(route)
                else:
                    check_length += 1
            if check_length == len(variable_list):
                return "NotSolved"
            f.close()
            return "Solved"
        else:
            return "NotSolved"

    def check(self):
        
        for route in self.solution_route:
            # print(route)

            ready_time = 0.
            total_demand = 0
            open_request = [] 
            for i in range(len(route)-1):

                # check PDP
                if route[i+1] in self.pickup:
                    open_request.append(route[i+1])
                if route[i+1] - EPS > int((self.end_depot-1)/2) and route[i+1] != self.end_depot:
                    if route[i+1] - int((self.end_depot-1)/2) in open_request:
                        open_request.remove(route[i+1] - int((self.end_depot-1)/2))
                    else:
                        return "Infsasible"

                # check demand
                total_demand += self.demands[route[i+1]]
                if total_demand - EPS > self.capacity:
                    return "Infsasible"

                # check compatibility
                if len(open_request) != 0 and route[i+1] in self.pickup:
                    for j in open_request:
                        if self.compatibility[self.commodity[j]-1][self.commodity[route[i+1]]-1] == 0:
                            return "Infsasible"

                # check time window
                trave_time = self.get_travel_time(route[i], route[i+1], ready_time)
                ready_time = ready_time + trave_time + self.service_times[route[i+1]]
                ready_time = max(ready_time, self.time_windows[route[i+1]][0] + self.service_times[route[i+1]])
                if ready_time - (self.time_windows[route[i+1]][1] + self.service_times[route[i+1]]) > EPS:
                    return "Infsasible"
            
            # there are open request
            if len(open_request) != 0:
                return "Infsasible"

        return "Fsasible"

def read_check(path1, path2, path3, number, algorithm):

    file_list = os.listdir(path1)
    customer_number = int(number)

    for filename in file_list:
        
        file_1 = path1 + filename
        file_2 = path2 + "CD_" + str(int(customer_number))  + ".csv"
        file_3 = path2 + "COMMODITY.csv"

        new_instance = instance(file_1, file_2, file_3)

        if new_instance.read_solution(path3, algorithm) == "NotSolved":
            print(new_instance.instance_name + "_" + algorithm + ": NotSolved")
        else:
            print(new_instance.instance_name + "_" + algorithm + ": " + new_instance.check())

    
if __name__ == "__main__":

    path_pdp = "Instances/Li-and-Lim-PDPTW/"
    path_commodity = "Instances/Commodity/"
    path_solution = "Sol_BPC_BP/"
    numbers = [10, 20, 30, 40, 50, 60, 80, 100]
    algorithms = ["BPC", "BP"]

    for algorithm in algorithms:
        for number in numbers:
            read_check(path_pdp, path_commodity, path_solution, number, algorithm)
