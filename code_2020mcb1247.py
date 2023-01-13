# ROHAN KUMAR 
# 2020MCB1247 

# Importing all the libraries
import bz2 
import re 
import xml.etree.ElementTree as ET
from collections import defaultdict
import random




# Function to remove brackets from a string. This is done because links are present as '[[Rohan]]' but we want 'Rohan'
def rem_bracket(ss): 
    s = ''
    for x in ss:
        # Removes '[' and ']' from the link text 
        if x != '[' and x != ']':
            s += x
    return s


# Function to extract desired links from a single webpage (using Regular Expressions and ElementTree)
def get_links(node): 
    outlinks = [] # List of all the links outgoing from this page 
    direct_links = [] # All links obtained from page text 
    for ch in node: 
        if ch.tag == 'revision': # In an XML page, the content of the page is under revision
            for gch in ch:
                if gch.tag == 'text': # In an XML page, the content is under text which is under revision 
                    link_text = gch.text
                    direct_links_brackets = re.findall(r'\[[- |\w]*?\]', str(link_text)) # Searches for all strings starting with '[' and ending with ']'
                    direct_links = [rem_bracket(x) for x in direct_links_brackets] # Removing brackets from the links 
    outlinks = outlinks + direct_links # Adding all links to final result
    for i in range(len(outlinks)):
        if '|' in outlinks[i]: 
            splits = list(outlinks[i].split('|'))
            outlinks[i] = splits[0]  # If we get link like 'Anarchism | Anarchy' then we take 'Anarchism', This is because 'Anarchism|Anarchy' redirects 
                                     # to Anarchism

    return outlinks


# Function to make a graph out of the wikidump and write it to a text file 
def bz2_to_graph(dump_file, graph_file):

    # We divide the XML data into pages using start and stop defined by us
    start = '<page>'
    stop = '</page>'

    # Adding the graph to a file for ease of use later on. We will only read that text file for later use. Extracting graph from the bz2 file takes too much time
    f = open(graph_file, "w", encoding = 'utf-8')

    # Reading the wikidata bz2 file line by line. 
    page = ''                                                                           # Starting a page 
                                                                                        # Page will store all the text between <page> and </page>

    track = 0                                                                           # Keeps track of the total webpages read till now 
    for line in  bz2.open(dump_file,mode = 'rt', encoding = 'utf-8'):
        text = line.rstrip('\n')

        # Splitting the XML file at each page
        if start in text: page = '' + start;continue
        if stop in text: 
            page += stop 

            # Creating Element tree of the current webpage. This object is basically stored as a root,
            # with all tags of that webpage present as children of that root
            root = ET.fromstring(page)
            page_links = get_links(root)

            # Adding the links to our graph 
            # A webpage will have each edge in a newline. To end webpage we use '---'. This symbol will be useful later on when we read graph from the text file. 
            f.write(root[0].text)
            f.write('\n')
            for child in page_links:
                f.write(child)
                f.write('\n')
            f.write('---') # Signifies the end of a webpage ( explained in readme file)
            f.write('\n')
            
            page = ''
            track += 1
            if track%5000 == 0:
                print('Number of Pages reached', track) # Prints the number of webpages read till now, at intervals of 10000 webpages
        page += text

    print('Pages have been read and file has been copied')
    f.close()





# Takes text file containing graph and creates a graph in the memory. Graph is stored as a dictionary   
def create_graph(graph_file):
    print('Reading Graph File....')
    # This is going to be our WikiGraph as an adjacency list. Random walk will run on this graph only 
    G = defaultdict(list)

    # Mapping numbers to pages. 
    # This is done because if we made graph using the names of the pages, then it will use too much memory. 
    # String size is much more than an integer. So we map pages to numbers to optimise memory 
    page_num = defaultdict(lambda : -1)  # This dictionary contains the pages and the numbers assigned to those pages 
    num_page = defaultdict()             # This dictionary contains the numbers as keys and the pages they represent as values 
    page_ct = [0]                        # This keeps track of the number of pages read till now. Used to assign a number to a webpage when it is discovered. 
                                         # For example, pf page_ct = [100], then the next unseen page will be assigned 101 


    # Function to map string to number (Basically we are assigning a number to each page)
    # This will help us conserve memory
    def str_to_num(name,page_ct):  
        if page_num[name] != -1:         # If the page is already in the page_num dictionary , then it returns it's number
            return page_num[name]
        else:                                        
            page_num[name] = page_ct[0] + 1  # Else it assigns the next available number to this unseen page 
            page_ct[0] += 1                  # Since we assigned a number to the new page, we increment this by 1 
            num_page[page_ct[0]] = name
            return page_num[name]           

    # Function to find the string of number
    def num_to_str(n):
        return num_page[n]      # We don't have to check if it's present in the dictionary or not. Because numbers only get assigned when names are read. 

    # Reading the graph that will be stored in our memory that we will use for our random walk. 
    # It is read from the text file we made containing the adjacency list of the wikigraph 
    f = open(graph_file, "r", encoding = 'utf-8')
    ct = 0 


    # Element will contain the page title and it's links as we go through a page
    # Element will be of the form [parent node, child node 1, child node 2....]
    # Hence element[0] is the title of the page  and rest are links 
    # Reason: I have stored adjacency list as follows : 
    # parent node
    # child node 1
    # child node 2
    # --- ( signifies end)
    

    element = []
    for line in f: 
        text = line.rstrip('\n')
        if text == '---': # We have reached the end of all links of a particular page 
            try: 
                parent_num = str_to_num(element[0],page_ct)  # element[0] will be the page title
                G[parent_num] = [str_to_num(x,page_ct) for x in element[1:]] # rest of the  elements are links so we add to graph G 
                
            except:  # To handle error cases ( handles nodes with no links or no title)
                #print('error at ',element)
                pass
                
            element = []  # Resets our element. Now we will move on to the links of the next page 
            ct += 1
            if ct%100000 == 0: print('Pages read:', ct) # Prints the number of pages read at intervals of 100000
        else:
            element.append(text) # Adding each link to our list(element) line by line
        

    print('Graph has been made')


    return G,page_num,num_page 
    # We have returned 3 items 
    # Returns Graph , The mapping of Webpage Names to Numbers and the mapping of numbers to names
    # The graph returned will not have nodes of webpage links, but the numbers assigned to each webpage
    # Example:  Anarchism may be assigned 3. It can be accessed later on by num_page[3] and page_num['Anarchism] will be 3.  

# Function to do a random walk on given graph and display the top k pages
def random_walk(G,page_num,num_page,k):
    print('Starting Random Walk ...')
    # This will be the dictionary that stores the frequency of visits of each node
    freq = defaultdict(int)

    # This is the list of all webpages. This list helps us teleport when we need to. 
    # We can choose a random element to teleport to. 
    keys_of_G = list(G.keys())

    # Choosing random node to start at 
    start = random.choice(keys_of_G) # Choosing start node at random 
    cur = start
    steps = 0 
    while(steps < 10000000):
        freq[cur] += 1 # Increasing the frequency of current node by 1 
        if_tp = 0 
        if random.random() <= 0.25: if_tp = 1 # Teleport with probability 0.14 so as to not get stuck in loops
        if if_tp:                           # Check whether to teleport or not 
            next = random.choice(keys_of_G) # Teleport to a random node 
        else:
            if len(G[cur]) != 0:
                next = random.choice(G[cur]) # Choose the next node from the current node's links  
            else:
                next = random.choice(keys_of_G) # Choose aa random node if current node has no links
        cur = next
        steps += 1
        if steps%1000000 == 0:      # Prints the steps at intervals of 1 million steps. Runs in approximately 2 seconds 
            print('steps',steps)
    

    print('Random Walk Finished')

    # Sort the resultant frequency dictionary in descending order and add the first k elements to result list. 
    # The result list contains tuples of the form (page name, frequency of visits to it)
    # Example: [(USA, 10000), (India, 8000), (China, 6900)]
    result_rw = [(num_page[x[0]],freq[x[0]]) for x in sorted(freq.items(), key=lambda x:-x[1])[:k]]
    

    # Display the resultant list of top k pages and their frequencies
    print('Results of Random Walk are as follows:')
    for item in result_rw:
        print(*item)
    

def main():
    # dump_file is the wiki dump file in bz2 format. 
    # If you want to use your own bz2 dump , change the name below 
    dump_file = 'wiki1.bz2'

    # graph_file is the file where the adjacency list of the graph is stored 
    # Assign the name of the text file you want to store your graph in to the variable graph_file 
    # This file must have adjacency list of my format. Otherwise reading of this file later on will not work 
    graph_file = 'full_wiki_graph.txt'

    # Writing the graph which we read from the dump_file to our graph_file
    #            (dump_file, graph_file)

    # Reading the written graph_file and creating a graph dictionary  
    # Note that create_graph returns 3 parameters and all are important for random walk 
    G,page_num,num_page = create_graph(graph_file)

    # If num_page[3] is run on my graph then it will return 'Anarchism 
    #print(num_page[3])

    # Choose steps of random walk here.  Or directly put your desired k in random_walk function when you run it. 
    k = 15

    # Running the random walk on resultant graph and displaying the top k pages 
    random_walk(G,page_num,num_page,k)

main()