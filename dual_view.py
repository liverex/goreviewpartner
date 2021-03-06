# -*- coding: utf-8 -*-

from Tkinter import *
from ScrolledText import *
import tkFont
import sys,time
from functools import partial
from toolbox import *
from toolbox import _

import os

from gtp import gtp
import ConfigParser

import threading, Queue

bg='#C0C0C0'

from goban import *

def get_node_number(node):
	k=0
	while node:
		node=node[0]
		if (node.get_move()[0]!=None) and (node.get_move()[1]!=None):
			k+=1
		else:
			break
	return k

def get_node(root,number=0):
	if number==0:return root
	node=root
	k=0
	while k!=number:
		if not node:
			return False
		node=node[0]
		k+=1
	return node


class OpenChart(Toplevel):
	def __init__(self,parent,data,nb_moves,current_move=0):
		Toplevel.__init__(self,parent)
		
		self.parent=parent
		self.nb_moves=nb_moves
		self.data=data
		self.current_move=current_move

		
		
		popup_width=self.parent.winfo_width()
		popup_height=self.parent.winfo_height()/2+10
		self.geometry(str(popup_width)+'x'+str(popup_height))
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		self.last_graph=Config.get("Review","LastGraph").decode("utf")
		self.initialize()

	def close(self):
		log("closing popup")
		self.destroy()
		self.parent.remove_popup(self)
		log("done")



	def initialize(self):
		
		    
		for widget in self.pack_slaves():
			widget.destroy()
		
		popup=self
		bg=popup.cget("background")
		
		top_frame=Frame(popup)
		top_frame.pack()
		
		self.graph_mode=StringVar()
		available_graphs=[]

		for data in self.data:
			if data:
				if "position_win_rate" in data:
					#self.graph_mode.set(_("Win rate")) # initialize
					available_graphs.append(_("Win rate"))
					break
		
		for data in self.data:
			if data:
				if "winrate_delta" in data:
					if data["player_color"]=="b":
						available_graphs.append(_("Black win rate delta"))
						break
		for data in self.data:
			if data:
				if "winrate_delta" in data:
					if data["player_color"]=="w":
						available_graphs.append(_("White win rate delta"))
						break
		
		for data in self.data:
			if data:
				if "monte_carlo_win_rate" in data:
					available_graphs.append(_("Monte Carlo win rate"))
					break
		
		for data in self.data:
			if data:
				if "mcwr_delta" in data:
					if data["player_color"]=="w":
						available_graphs.append(_("Black Monte Carlo win rate delta"))
						break

		for data in self.data:
			if data:
				if "mcwr_delta" in data:
					if data["player_color"]=="b":
						available_graphs.append(_("White Monte Carlo win rate delta"))
						break
		
		for data in self.data:
			if data:
				if "value_network_win_rate" in data:
					available_graphs.append(_("Value Network win rate"))
					break
		
		for data in self.data:
			if data:
				if "vnwr_delta" in data:
					if data["player_color"]=="w":
						available_graphs.append(_("Black Value Network win rate delta"))
						break

		for data in self.data:
			if data:
				if "vnwr_delta" in data:
					if data["player_color"]=="b":
						available_graphs.append(_("White Value Network win rate delta"))
						break
		
		for data in self.data:
			if data:
				if ("score_estimation" in data) or ("upper_bound_score" in data) or ("lower_bound_score" in data):
					#self.graph_mode.set(_("Score estimation")) # initialize
					available_graphs.append(_("Score estimation"))
					break
		
		self.graph_selection=apply(OptionMenu,(top_frame,self.graph_mode)+tuple(available_graphs))
		self.graph_selection.pack(side=LEFT, padx=5)
		if self.last_graph in [mode.decode("utf") for mode in available_graphs]:
			self.graph_mode.set(self.last_graph)
		else:
			self.last_graph=available_graphs[0].decode("utf")
			self.graph_mode.set(self.last_graph)
			
		self.graph_mode.trace("w", lambda a,b,c: self.change_graph())
		self.chart = Canvas(popup,bg='white',bd=0, borderwidth=0)
		#self.chart.grid(sticky=N+S+W+E)
		
		self.chart.pack(fill=BOTH,expand=1, padx=5)
		self.chart.bind("<Configure>",self.display)
		
		bottom_frame=Frame(popup)
		bottom_frame.pack(anchor=W)
		
		self.status_bar=Label(bottom_frame,text='',background=bg)
		self.status_bar.pack(anchor=W)
		bottom_frame.pack()
	
		self.clear_status()
		self.bind('<Control-q>', self.save_as_png)
		
		self.protocol("WM_DELETE_WINDOW", self.close)
		popup.focus()
	
	def set_status(self,event=None,msg=''):
		self.status_bar.config(text=msg)
	
	def clear_status(self,event=None):
		self.status_bar.config(text=_("<Ctrl+Q> to save the graph as an image."))
	
	def goto_move(self,event=None,move=None):
		if move:
			log("goto move",move)
			self.parent.parent.lift()			
			self.parent.goto_move(move_number=move)
		
	
	def display_vertical_winrate_graduation(self,border,height,width):
		#drawing vertical graduation
		lpix=int(border/4)
		graduations=[x*10 for x in range(10+1)]
		y0=height+1000
		x0=border/2
		x1=width-border/2
		for g in graduations:
			y1=height-border-g*(height-2*border)/100.
			
			if y0-y1>=border:
				self.chart.create_text(x0,y1, text=str(g)+"%",fill='black',font=("Arial", str(lpix)))
				self.chart.create_text(x1,y1, text=str(g)+"%",fill='black',font=("Arial", str(lpix)))
				#self.chart.create_line(x0, y1, x1, y1, fill='black')
				y0=y1
	
	def display_vertical_score_graduation(self,border,height,width,maximum):
		#drawing vertical graduation
		lpix=int(border/4)
		graduations=[x*20 for x in range(int(-maximum/20.),int((maximum+20)/20.))]
		y0=height+1000
		x0=border/2
		x1=width-border/2
		middle=height-border-(height-2*border)/2
		for g in graduations:
			y1=height-border-g*(height-2*border)/100.
			y1=g/2*(height-2*border)/maximum
			y1=middle-y1
			if y0-y1>=border:
				self.chart.create_text(x0,y1, text=str(g),fill='black',font=("Arial", str(lpix)))
				self.chart.create_text(x1,y1, text=str(g),fill='black',font=("Arial", str(lpix)))
				#self.chart.create_line(x0, y1, x1, y1, fill='black')
				y0=y1
	
	def change_graph(self,event=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		self.last_graph=_(self.graph_mode.get())
		if type(self.last_graph)!=type(u"utf"):
			self.last_graph=self.last_graph.decode("utf8")
		
		Config.set("Review","LastGraph",self.last_graph.encode("utf"))
		Config.write(open(config_file,"w"))
		self.display()
		
	def display(self,event=None):
		if event:
			width=event.width
			height=event.height
			self.width=width
			self.height=height
		else:
			width=self.width
			height=self.height
		
		border=min(max(20,width/25),200)
		space=1.0*(width-2*border)/self.nb_moves
		lpix=int(border/4)
		
		for item in self.chart.find_all():
			self.chart.delete(item)
		
		self.chart.create_line(0, 0, width, 0, fill='#000000',width=4)
		self.chart.create_line(0, height, width, height, fill='#000000',width=4)
		self.chart.create_line(0, 0, 0, height, fill='#000000',width=4)
		self.chart.create_line(width, 0, width, height, fill='#000000',width=4)
		
		y00=height-border
		x0=border+(self.current_move-1)*space
		x1=x0+space
		y1=border
		yellow_bar=self.chart.create_rectangle(x0, y00, x1, y1, fill='#FFFF00',outline='#FFFF00')
		
		mode=self.last_graph

		if mode in (_("Black win rate delta").decode("utf"),_("White win rate delta").decode("utf")):
			moves=self.display_winrate_delta(border,height,width)
		elif mode==_("Win rate").decode("utf"):
			moves=self.display_winrate_graph(border,height,width,lpix)
		elif mode==_("Score estimation").decode("utf"):
			moves=self.display_score_graph(border,height,width,lpix)
		elif mode==_("Monte Carlo win rate").decode("utf"):
			moves=self.display_monte_carlo_winrate_graph(border,height,width,lpix)
		elif mode==_("Value Network win rate").decode("utf"):
			moves=self.display_value_network_winrate_graph(border,height,width,lpix)
		elif mode in (_("Black Monte Carlo win rate delta").decode("utf"),_("White Monte Carlo win rate delta").decode("utf")):
			moves=self.display_monte_carlo_delta(border,height,width)
		elif mode in (_("Black Value Network win rate delta").decode("utf"),_("White Value Network win rate delta").decode("utf")):
			moves=self.display_value_network_delta(border,height,width)
		
		self.display_horizontal_graduation(moves,height,width,border,lpix)
		self.display_axis(moves,height,width,border,lpix)

	def display_value_network_delta(self,border,height,width):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		if self.graph_mode.get()=="Black Value Network win rate delta":
			player_color='b'
		else:
			player_color='w'

		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if (one_data["player_color"]==player_color) and ("vnwr_delta" in one_data):
				position_win_rate=one_data["value_network_win_rate"]
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space*2
				
				y0=height-border
				y1=height-border-position_win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				delta=one_data["vnwr_delta"]
				
				if player_color.lower()=="b":
					msg=_("Move %i: Black's move win rate: %s, computer's move win rate: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				else:
					msg=_("Move %i: White's move win rate: %s, computer's move win rate: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				if delta<>0:
					y2=y1-delta*(height-2*border)/100.
					if delta<0:
						red_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='red',outline='#aa0000')
						msg2=_("The computer believes it's own move win rate would be %.2fpp higher.")%(-delta)
						self.chart.tag_bind(red_bar, "<Enter>", partial(self.set_status,msg=msg2))
						self.chart.tag_bind(red_bar, "<Leave>", self.clear_status)
						self.chart.tag_bind(red_bar, "<Button-1>",partial(self.goto_move,move=move))
					else:
						green_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='#00ff00',outline='#00aa00')
						msg2=_("The computer believes the actual move is %.2fpp better than it's best move.")%(delta)
						self.chart.tag_bind(green_bar, "<Enter>", partial(self.set_status,msg=msg2))
						self.chart.tag_bind(green_bar, "<Leave>", self.clear_status)
						self.chart.tag_bind(green_bar, "<Button-1>",partial(self.goto_move,move=move))
						
				self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
				self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
				x00=x1
				y00=y1
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves

	def display_monte_carlo_delta(self,border,height,width):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		if self.graph_mode.get()=="Black Monte Carlo win rate delta":
			player_color='b'
		else:
			player_color='w'

		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if (one_data["player_color"]==player_color) and ("mcwr_delta" in one_data):
				position_win_rate=one_data["monte_carlo_win_rate"]
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space*2
				
				y0=height-border
				y1=height-border-position_win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				delta=one_data["mcwr_delta"]
				
				if player_color.lower()=="b":
					msg=_("Move %i: Black's move win rate: %s, computer's move win rate: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				else:
					msg=_("Move %i: White's move win rate: %s, computer's move win rate: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				if delta<>0:
					y2=y1-delta*(height-2*border)/100.
					if delta<0:
						red_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='red',outline='#aa0000')
						msg2=_("The computer believes it's own move win rate would be %.2fpp higher.")%(-delta)
						self.chart.tag_bind(red_bar, "<Enter>", partial(self.set_status,msg=msg2))
						self.chart.tag_bind(red_bar, "<Leave>", self.clear_status)
						self.chart.tag_bind(red_bar, "<Button-1>",partial(self.goto_move,move=move))
					else:
						green_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='#00ff00',outline='#00aa00')
						msg2=_("The computer believes the actual move is %.2fpp better than it's best move.")%(delta)
						self.chart.tag_bind(green_bar, "<Enter>", partial(self.set_status,msg=msg2))
						self.chart.tag_bind(green_bar, "<Leave>", self.clear_status)
						self.chart.tag_bind(green_bar, "<Button-1>",partial(self.goto_move,move=move))
						
				self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
				self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
				x00=x1
				y00=y1
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves

	def display_winrate_delta(self,border,height,width):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		if self.graph_mode.get()=="Black win rate delta":
			player_color='b'
		else:
			player_color='w'

		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if (one_data["player_color"]==player_color) and ("winrate_delta" in one_data):
				position_win_rate=one_data["position_win_rate"]
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space*2
				
				y0=height-border
				y1=height-border-position_win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				delta=one_data["winrate_delta"]
				
				if player_color.lower()=="b":
					msg=_("Move %i: Black's move win rate: %s, computer's move win rate: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				else:
					msg=_("Move %i: White's move win rate: %s, computer's move win rate: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				if delta<>0:
					y2=y1-delta*(height-2*border)/100.
					if delta<0:
						red_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='red',outline='#aa0000')
						msg2=_("The computer believes it's own move win rate would be %.2fpp higher.")%(-delta)
						self.chart.tag_bind(red_bar, "<Enter>", partial(self.set_status,msg=msg2))
						self.chart.tag_bind(red_bar, "<Leave>", self.clear_status)
						self.chart.tag_bind(red_bar, "<Button-1>",partial(self.goto_move,move=move))
					else:
						green_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='#00ff00',outline='#00aa00')
						msg2=_("The computer believes the actual move is %.2fpp better than it's best move.")%(delta)
						self.chart.tag_bind(green_bar, "<Enter>", partial(self.set_status,msg=msg2))
						self.chart.tag_bind(green_bar, "<Leave>", self.clear_status)
						self.chart.tag_bind(green_bar, "<Button-1>",partial(self.goto_move,move=move))
						
				self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
				self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
				x00=x1
				y00=y1
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves

	def display_value_network_winrate_graph(self,border,height,width,lpix):
		moves=[]
		space=1.0*(width-2*border)/self.nb_moves
		
		self.chart.create_text(len(_("Black win rate"))*lpix/2,border/2, text=_("Black win rate"),fill='black',font=("Arial", str(lpix)))
		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if "value_network_win_rate" in one_data:
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space
				
				win_rate=one_data["value_network_win_rate"]
				if one_data["player_color"]=="w":
					win_rate=100.-win_rate
					color=_("White")
				else:
					color=_("Black")
				player_win_rate=float(int(win_rate*100)/100.)
				y0=height-border
				y1=height-border-win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				#msg="Move "+str(move)+" ("+color+"), black/white win rate: "+str(player_win_rate)+"%/"+str(100-player_win_rate)+"%"
				msg=(_("Move %i (%s), black/white win rate: ")%(move,color))+str(win_rate)+"%/"+str(100-player_win_rate)+"%"
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
				self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
				x00=x1
				y00=y1
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves
		
	def display_monte_carlo_winrate_graph(self,border,height,width,lpix):
		moves=[]
		space=1.0*(width-2*border)/self.nb_moves
		
		self.chart.create_text(len(_("Black win rate"))*lpix/2,border/2, text=_("Black win rate"),fill='black',font=("Arial", str(lpix)))
		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if "monte_carlo_win_rate" in one_data:
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space
				
				win_rate=one_data["monte_carlo_win_rate"]
				if one_data["player_color"]=="w":
					win_rate=100.-win_rate
					color=_("White")
				else:
					color=_("Black")
				player_win_rate=float(int(win_rate*100)/100.)
				y0=height-border
				y1=height-border-win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				#msg="Move "+str(move)+" ("+color+"), black/white win rate: "+str(player_win_rate)+"%/"+str(100-player_win_rate)+"%"
				msg=(_("Move %i (%s), black/white win rate: ")%(move,color))+str(win_rate)+"%/"+str(100-player_win_rate)+"%"
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
				self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
				x00=x1
				y00=y1
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves


	def display_winrate_graph(self,border,height,width,lpix):
		moves=[]
		space=1.0*(width-2*border)/self.nb_moves
		
		self.chart.create_text(len(_("Black win rate"))*lpix/2,border/2, text=_("Black win rate"),fill='black',font=("Arial", str(lpix)))
		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if "position_win_rate" in one_data:
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space
				
				position_win_rate=one_data["position_win_rate"]
				if one_data["player_color"]=="w":
					position_win_rate=100.-position_win_rate
					color=_("White")
				else:
					color=_("Black")
				player_win_rate=float(int(position_win_rate*100)/100.)
				y0=height-border
				y1=height-border-position_win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				#msg="Move "+str(move)+" ("+color+"), black/white win rate: "+str(player_win_rate)+"%/"+str(100-player_win_rate)+"%"
				msg=(_("Move %i (%s), black/white win rate: ")%(move,color))+str(position_win_rate)+"%/"+str(100-player_win_rate)+"%"
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
				self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
				x00=x1
				y00=y1
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves

	def display_score_graph(self,border,height,width,lpix):
		self.chart.create_text(border+len(_("Black win"))*lpix/2,border+lpix, text=_("Black win"),fill='black',font=("Arial", str(lpix)))
		self.chart.create_text(border+len(_("White win"))*lpix/2,height-border-lpix, text=_("White win"),fill='black',font=("Arial", str(lpix)))
		moves=[]
		#checking graph limits
		maximum=-1000
		for one_data in self.data:
			if "score_estimation" in one_data:
				maximum=max(maximum,max([abs(x) for x in (one_data["upper_bound_score"],one_data["lower_bound_score"],one_data["score_estimation"])]))
		maximum+=5
		space=1.0*(width-2*border)/self.nb_moves
		middle=height-border-(height-2*border)/2
		x00=border
		y00=middle
		for one_data in self.data:
			if "score_estimation" in one_data:
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space
				estimated_score=one_data["score_estimation"]
				upper_bound_score=one_data["upper_bound_score"]
				lower_bound_score=one_data["lower_bound_score"]

				y0=middle-lower_bound_score*(height-2*border)/2./maximum
				y1=middle-upper_bound_score*(height-2*border)/2./maximum
				y2=middle-estimated_score*(height-2*border)/2./maximum
				y3=min(middle,y0,y1,y2)
				y4=max(middle,y0,y1,y2)
				
				white_bar=self.chart.create_rectangle(x0, y3, x1, y4, fill='#eeeeee',outline='')


				self.chart.create_line(x0, y2, x1, y2, fill='#0000ff',width=2)
				self.chart.create_line(x0, y2, x00, y00, fill='#0000ff')
				x00=x1
				y00=y2					
				
				if one_data["player_color"]=="w":
					color=_("White")
				else:
					color=_("Black")
				
				if estimated_score>=0:
					msg=(_("Move %i (%s), estimated score: ")%(move,color))
					msg+="B+"+str(estimated_score)
					if (lower_bound_score!=upper_bound_score):
						msg+=" [B%+.1f, B%+.1f]"%(lower_bound_score,upper_bound_score)
				else:
					msg=(_("Move %i (%s), estimated score: ")%(move,color))
					msg+="W+"+str(abs(estimated_score))
					if (lower_bound_score!=upper_bound_score):
						msg+=" [W%+.1f, W%+.1f]"%(-lower_bound_score,-upper_bound_score)
				
				self.chart.tag_bind(white_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(white_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(white_bar, "<Button-1>",partial(self.goto_move,move=move))
				if y0!=y1:
					grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
					self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
					self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
					self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
					self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
					self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
					self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
			
		self.display_vertical_score_graduation(border,height,width,maximum)
		return moves

	def display_axis(self,moves,height,width,border,lpix):
		#drawing axis
		x0=border
		y0=height-border
		y1=border
		self.chart.create_line(x0, y0, x0, y1, fill='black')
		x1=width-border
		self.chart.create_line(x1, y0, x1, y1, fill='black')
		self.chart.create_line(x0, y0, x1, y0, fill='black')
		self.chart.create_line(x0, (y0+y1)/2, x1, (y0+y1)/2, fill='black')
	
	def display_horizontal_graduation(self,moves,height,width,border,lpix):
		#drawing horizontal graduation
		graduations=[x for x in moves]
		x0=-1000
		y0=height-border/2
		y1=height-border
		for g in graduations:
			x1=border+(g)*(width-2*border)/self.nb_moves*1.0
			
			if x1-x0>=border:
				self.chart.create_text(x1,y0, text=str(g),fill='black',font=("Arial", str(lpix)))
				self.chart.create_line(x1, y1, x1, (y0+y1)/2, fill='black')
				x0=x1
		
		
	def save_as_png(self,e=None):
		filename=save_png_file(filename=self.graph_mode.get()+' graph.png',parent=self)
		canvas2png(self.chart,filename)


class OpenMove(Toplevel):
	def __init__(self,parent,move,dim,sgf,goban_size=200):
		Toplevel.__init__(self,parent)
		self.parent=parent
		self.move=move
		self.dim=dim
		self.sgf=sgf
		self.goban_size=goban_size
		
		self.available_bots=[]
		for bot in get_available("ReviewBot"):
			self.available_bots.append(bot)
		self.initialize()
		
	def lock(self):	
		self.undo_button.config(state='disabled')
		self.menu.config(state='disabled')
		self.play_button.config(state='disabled')
		self.white_button.config(state='disabled')
		self.black_button.config(state='disabled')
		self.evaluation_button.config(state='disabled')
		
		if (not self.white_autoplay) or (not self.black_autoplay):
			self.selfplay_button.config(state='disabled')

		self.goban.bind("<Button-1>",self.do_nothing)
		self.goban.bind("<Button-2>",self.do_nothing)
		self.locked=True

	def do_nothing(self):
		pass

	def unlock(self):
		self.undo_button.config(state='normal')
		self.menu.config(state='normal')
		self.play_button.config(state='normal')
		self.white_button.config(state='normal')
		self.black_button.config(state='normal')
		self.selfplay_button.config(state='normal')
		self.evaluation_button.config(state='normal')
		self.goban.bind("<Button-1>",self.click)
		self.goban.bind("<Button-2>",self.undo)
		self.locked=False
		
	def close(self):
		log("closing popup")
		self.display_queue.put(0)
		self.destroy()
		
		for bot in self.bots:
			bot.close()

		self.parent.remove_popup(self)
		log("done")
	
	def undo(self,event=None):
		log("UNDO")
		if self.undo_button.cget("state")=='disabled':
			return
		if len(self.history)<1:
			return
		elif len(self.history)==1:
			self.undo_button.config(state='disabled')
		
		self.grid,self.markup=self.history.pop()
		self.next_color=3-self.next_color
		self.goban.display(self.grid,self.markup)
		
		for bot in self.bots:
			bot.undo()
		

	def click_button(self,bot):
		dim=self.dim
		self.lock()
		self.display_queue.put(2)
		color=self.next_color
		move=bot.click(color)
		
		if move.lower() not in ["pass","resign"]:
			i,j=gtp2ij(move)
			#log('i,j=',i,j)
			
			for other_bot in self.bots:
				if other_bot!=bot:
					try:
						other_bot.place(move,color)
					except:
						pass
			
			self.history.append([copy(self.grid),copy(self.markup)])
			
			place(self.grid,i,j,color)
			self.grid[i][j]=color
			self.markup=[["" for row in range(dim)] for col in range(dim)]
			self.markup[i][j]=0
			self.next_color=3-color
		else:
			if move.lower() == "resign":
				bot.undo_resign()
			else:
				bot.undo()
			if color==1:
				self.display_queue.put(bot.name+" ("+_("Black")+"): "+move.lower())
			else:
				self.display_queue.put(bot.name+" ("+_("White")+"): "+move.lower())
		
		if self.white_autoplay and self.black_autoplay:
			if move.lower() not in ["pass","resign"]:
				log("SELF PLAY")
				self.display_queue.put(2)
				
				one_thread=threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],))
				self.after(0,one_thread.start)
				return
			else:
				log("End of SELF PLAY")
				self.click_selfplay()
				self.display_queue.put(1)
				self.unlock()
				return
		else:
			self.display_queue.put(1)
			self.unlock()
			return
		
		
		
	def click(self,event):
		dim=self.dim
		#add/remove black stone
		#check pointer location
		i,j=self.goban.xy2ij(event.x,event.y)
		color=self.next_color
		if 0 <= i <= dim-1 and 0 <= j <= dim-1:
			#inside the grid
			#what is under the pointer ?
			
			if self.grid[i][j] not in (1,2):
				#nothing, so we add a black stone			
				for bot in self.bots:
					if bot.place(ij2gtp((i,j)),color)==False:
						del self.menu_bots[bot.name]
						self.menu.pack_forget()
						if len(self.menu_bots):
							self.selected_bot.set(self.menu_bots.keys()[0])
							self.selected_bot=StringVar()
							#self.menu=OptionMenu(self.menu_wrapper,self.selected_bot,*tuple(self.menu_bots.keys()))
							self.menu=apply(OptionMenu, (self.menu_wrapper, self.selected_bot) + tuple(self.menu_bots.keys()))
							self.menu.pack(fill=BOTH,expand=1)
						else:
							self.menu.config(state='disabled')
							self.play_button.config(state='disabled')
							self.white_button.config(state='disabled')
							self.black_button.config(state='disabled')
							self.selfplay_button.config(state='disabled')
							
				self.history.append([copy(self.grid),copy(self.markup)])
					
				place(self.grid,i,j,color)
				self.grid[i][j]=color
					
				self.markup=[["" for row in range(dim)] for col in range(dim)]
				self.markup[i][j]=0
					
				self.goban.display(self.grid,self.markup)
				self.next_color=3-color
				self.undo_button.config(state='normal')
				
				if color==1:
					if self.white_autoplay:
						threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
						#self.click_button(self.menu_bots[self.selected_bot.get()])
				else:
					if self.black_autoplay:
						threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
						#self.click_button(self.menu_bots[self.selected_bot.get()])
						
	def set_status(self,msg,event=None):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")
	
	def click_play_one_move(self):
		log("Asking",self.selected_bot.get(),"to play one move")
		self.white_button.config(relief=RAISED)
		self.black_button.config(relief=RAISED)
		self.selfplay_button.config(relief=RAISED)
		
		self.black_autoplay=False
		self.white_autoplay=False
		
		threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
		#self.click_button(self.menu_bots[self.selected_bot.get()])


	def click_white_answer(self):
		
		if self.white_button.cget("relief")!=SUNKEN:
			self.white_button.config(relief=SUNKEN)
			self.white_autoplay=True
		else:
			self.white_button.config(relief=RAISED)
			self.white_autoplay=False
		
		self.black_autoplay=False
		
		self.black_button.config(relief=RAISED)
		self.selfplay_button.config(relief=RAISED)
		
	def click_black_answer(self):
		
		if self.black_button.cget("relief")!=SUNKEN:
			self.black_button.config(relief=SUNKEN)
			self.black_autoplay=True
		else:
			self.black_button.config(relief=RAISED)
			self.black_autoplay=False
		
		self.white_autoplay=False
		
		self.white_button.config(relief=RAISED)
		self.selfplay_button.config(relief=RAISED)

	def click_selfplay(self):
		self.white_button.config(relief=RAISED)
		self.black_button.config(relief=RAISED)
		if self.selfplay_button.cget("relief")!=SUNKEN:
			if self.locked:
				self.selfplay_button.config(relief=RAISED)
				return
			self.selfplay_button.config(relief=SUNKEN)
			self.black_autoplay=True
			self.white_autoplay=True
			self.selfplay_button.config(text=_('Abort'))
			threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
		else:
			self.selfplay_button.config(relief=RAISED)
			self.black_autoplay=False
			self.white_autoplay=False
			self.selfplay_button.config(text=_('Self play'))
	
	def click_evaluation(self):
		log("Asking",self.selected_bot.get(),"for quick estimation")
		self.lock()
		self.display_queue.put(2)
		threading.Thread(target=self.evaluation,args=(self.menu_bots[self.selected_bot.get()],)).start()
	
	def evaluation(self,bot):
		color=self.next_color
		result=bot.quick_evaluation(color)
		if color==1:
			self.display_queue.put(result)
		else:
			self.display_queue.put(result)
		self.unlock()
	
	def initialize(self):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		sgf=self.sgf
		komi=self.sgf.get_komi()
		gameroot=self.sgf.get_root()
		
		popup=self
		
		dim=self.dim
		move=self.move
		
		#popup.configure(background=bg)
		bg=popup.cget("background")
		self.locked=False
		panel=Frame(popup, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)
		panel.configure(background=bg)
		
		
		undo_button=Button(panel, text=_('Undo'),command=self.undo)
		undo_button.grid(column=0,row=1,sticky=E+W)
		undo_button.config(state='disabled')
		undo_button.bind("<Enter>",lambda e: self.set_status(_("Undo last move. Shortcut: mouse middle button.")))
		undo_button.bind("<Leave>",lambda e: self.clear_status())
		
		self.bots=[]
		self.menu_bots={}
		row=10
		value={"slow":" (%s)"%_("Slow profile"),"fast":" (%s)"%_("Fast profile")}
		for available_bot in self.available_bots:
			row+=2
			one_bot=available_bot['openmove'](self.sgf,available_bot['profile'])
			one_bot.start()
			self.bots.append(one_bot)
			if one_bot.okbot:
				self.menu_bots[one_bot.name+value[available_bot['profile']]]=one_bot

		if len(self.menu_bots)>0:
			
			row+=10
			Label(panel,text=" ").grid(column=0,row=row,sticky=E+W)
			
			row+=1
			self.selected_bot=StringVar()
			self.selected_bot.set(self.menu_bots.keys()[0])
			
			self.menu_wrapper=Frame(panel)
			self.menu_wrapper.grid(row=row,column=0,sticky=E+W)
			self.menu_wrapper.bind("<Enter>",lambda e: self.set_status(_("Select a bot.")))
			self.menu_wrapper.bind("<Leave>",lambda e: self.clear_status())
			
			#self.menu=OptionMenu(self.menu_wrapper,self.selected_bot,*tuple(self.menu_bots.keys()))
			self.menu=apply(OptionMenu, (self.menu_wrapper, self.selected_bot) + tuple(self.menu_bots.keys()))
			self.menu.pack(fill=BOTH,expand=1)
			
			row+=1
			Label(panel,text=" ").grid(column=0,row=row,sticky=E+W)
			
			row+=1
			self.play_button=Button(panel, text=_('Play one move'),command=self.click_play_one_move)
			self.play_button.grid(column=0,row=row,sticky=E+W)
			self.play_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot to play one move.")))
			self.play_button.bind("<Leave>",lambda e: self.clear_status())
			
			
			row+=1
			self.white_button=Button(panel, text=_('Play as white'),command=self.click_white_answer)
			self.white_button.grid(column=0,row=row,sticky=E+W)
			self.white_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot to play as White.")))
			self.white_button.bind("<Leave>",lambda e: self.clear_status())
			
			row+=1
			self.black_button=Button(panel, text=_('Play as black'),command=self.click_black_answer)
			self.black_button.grid(column=0,row=row,sticky=E+W)
			self.black_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot to play as Black.")))
			self.black_button.bind("<Leave>",lambda e: self.clear_status())
			
			row+=1
			self.selfplay_button=Button(panel, text=_('Self play'),command=self.click_selfplay)
			self.selfplay_button.grid(column=0,row=row,sticky=E+W)
			self.selfplay_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot to play alone.")))
			self.selfplay_button.bind("<Leave>",lambda e: self.clear_status())
		
			row+=1
			Label(panel,text=" ").grid(column=0,row=row,sticky=E+W)
			row+=1
			self.evaluation_button=Button(panel, text=_('Quick evaluation'),command=self.click_evaluation)
			self.evaluation_button.grid(column=0,row=row,sticky=E+W)
			self.evaluation_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot for a quick evaluation")))
			self.evaluation_button.bind("<Leave>",lambda e: self.clear_status())
			
		
		self.black_autoplay=False
		self.white_autoplay=False
		
		panel.grid(column=1,row=1,sticky=N+S)
		
		goban3 = Goban(dim,master=popup, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		goban3.space=self.goban_size/(dim+1+1)
		goban3.grid(column=2,row=1,sticky=N+S+E+W)
		popup.grid_rowconfigure(1, weight=1)
		popup.grid_columnconfigure(2, weight=1)
		
		
		self.bind('<Control-q>', self.save_as_png)
		goban3.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+Q> to save the goban as an image.")))
		goban3.bind("<Leave>",lambda e: self.clear_status())
		
		Label(popup,text='   ',background=bg).grid(row=0,column=3)
		Label(popup,text='   ',background=bg).grid(row=2,column=0)
		
		self.status_bar=Label(popup,text='',background=bg)
		self.status_bar.grid(row=2,column=1,columnspan=2,sticky=W)
		
		grid3=[[0 for row in range(dim)] for col in range(dim)]
		markup3=[["" for row in range(dim)] for col in range(dim)]
		
		log("========================")
		log("opening move",move)
		
		board, noneed = sgf_moves.get_setup_and_moves(self.sgf)
		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				color=1
			else:
				color=2
			place(grid3,row,col,color)

		m=0
		for m in range(1,move):
			one_move=get_node(gameroot,m)
			if one_move==False:
				log("(0)leaving because one_move==False")
				return
			
			ij=one_move.get_move()[1]
			
			#log(ij)
			
			if one_move.get_move()[0]=='b':
				color=1
			else:
				color=2
			
			for bot in self.bots:
				bot.place(ij2gtp(ij),color)
			
			if ij==None:
				log("(1)skipping because ij==None",ij)
				continue

			i,j=ij
			place(grid3,i,j,color)
		
		if m>0:
			markup3[i][j]=0
		
		try:
			if get_node(gameroot,move).get_move()[0].lower()=="w":
				self.next_color=2
			else:
				self.next_color=1
		except:
			log("error when trying to figure out next color to play, so black is selected")
			self.next_color=1
		goban3.display(grid3,markup3)
		
		self.goban=goban3
		self.grid=grid3
		self.markup=markup3

		self.undo_button=undo_button
		
		popup.protocol("WM_DELETE_WINDOW", self.close)
		goban3.bind("<Button-1>",self.click)
		goban3.bind("<Button-2>",self.undo)
		#goban3.bind("<Button-3>",lambda event: click_on_undo(popup))
		
		self.history=[]

		self.goban.bind("<Configure>",self.redraw)
		popup.focus()
		
		self.display_queue=Queue.Queue(1)
		self.parent.after(100,self.wait_for_display)
	
	def wait_for_display(self):
		try:
			msg=self.display_queue.get(False)
			
			if msg==0:
				pass
			elif msg==1:
				self.goban.display(self.grid,self.markup)
				self.parent.after(250,self.wait_for_display)
			elif msg==2:
				self.goban.display(self.grid,self.markup,True)
				self.parent.after(250,self.wait_for_display)
			else:
				show_info(msg,self)
				self.goban.display(self.grid,self.markup)
				self.parent.after(0,self.wait_for_display)
		except:
			self.parent.after(250,self.wait_for_display)
		
	
	def redraw(self, event):
		new_size=min(event.width,event.height)
		new_space=new_size/(self.dim+1+1)
		self.goban.space=new_space
		
		new_anchor_x=(event.width-new_size)/2.
		self.goban.anchor_x=new_anchor_x
		
		new_anchor_y=(event.height-new_size)/2.
		self.goban.anchor_y=new_anchor_y
		
		self.goban.redraw()

	def save_as_png(self,e=None):
		filename = save_png_file(parent=self,filename='variation_move'+str(self.move)+'.png')
		canvas2png(self.goban,filename)
		
class DualView(Toplevel):
	def __init__(self,parent,filename,goban_size=200):
		Toplevel.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		self.goban_size=goban_size
		
		global Config, goban
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		goban.fuzzy=float(Config.get("Review", "FuzzyStonePlacement"))
		self.variation_color_mode=Config.get("Review", "VariationsColoring")
		self.inverted_mouse_wheel=Config.getboolean('Review', 'InvertedMouseWheel')

		self.initialize()
		
		self.current_move=1
		self.display_move(self.current_move)

		self.pressed=0
		self.parent.focus()
	
	def remove_popup(self,popup):
		log("Removing popup")
		self.popups.remove(popup)

	def add_popup(self,popup):
		log("Adding new popup")
		self.popups.append(popup)

	def close(self):
		for popup in self.popups[:]:
			popup.close()
		self.destroy()
		self.parent.remove_popup(self)
	
	def prev_10_move(self,event=None):
		self.current_move=max(1,self.current_move-10)
		self.pressed=time.time()
		pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
		self.parent.after(0,lambda: pf())

	def prev_move(self,event=None):
		if self.current_move>1:
			self.pressed=time.time()
			self.current_move-=1
			pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
			self.parent.after(0,lambda: pf())
	
	def next_10_move(self,event=None):
		self.current_move=min(get_node_number(self.gameroot),self.current_move+10)
		self.pressed=time.time()
		pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
		self.parent.after(0,lambda: pf())
	
	def next_move(self,event=None):
		if self.current_move<get_node_number(self.gameroot):
			self.pressed=time.time()
			self.current_move+=1
			pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
			self.parent.after(0,lambda: pf())
			
	def first_move(self,event=None):
		self.current_move=1
		self.pressed=time.time()
		pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
		self.parent.after(0,lambda: pf())
		
	def final_move(self,event=None):
		self.current_move=get_node_number(self.gameroot)
		self.pressed=time.time()
		pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
		self.parent.after(0,lambda: pf())
	

	def goto_move(self,move_number,pressed=None):
		self.move_number.config(text=str(move_number)+'/'+str(get_node_number(self.gameroot)))
		
		if not pressed:
			self.current_move=move_number
			self.display_move(self.current_move)
			for popup in self.popups:
				if isinstance(popup,OpenChart):
					popup.current_move=self.current_move
					#self.parent.after(0,popup.display)
					popup.display()
		
		elif self.pressed==pressed:
			self.display_move(self.current_move)
			for popup in self.popups:
				if isinstance(popup,OpenChart):
					popup.current_move=self.current_move
					#self.parent.after(0,popup.display)
					popup.display()

		self.update_idletasks()
		
	def leave_variation(self,goban,grid,markup):
		self.comment_box2.delete(1.0, END)
		self.parent.bind("<Up>", lambda e: None)
		self.parent.bind("<Down>", lambda e: None)
		self.current_variation_sequence=None
		self.clear_status()
		goban.display(grid,markup)

	def show_variation(self,event,goban,grid,markup,i,j):
		sequence=markup[i][j]
		self.show_variation_move(goban,grid,markup,i,j,len(sequence))
	
	
	def show_variation_move(self,goban,grid,markup,i,j,move):
		sequence=markup[i][j]
		temp_grid=copy(grid)
		temp_markup=copy(markup)
		
		for u in range(self.dim):
			for v in range(self.dim):
				if temp_markup[u][v]!=0:
					temp_markup[u][v]=''
		
		k=1
		for color,(u,v),s,comment,displaycolor,letter_color in sequence[:move]:
			#temp_grid[u][v]=color
			place(temp_grid,u,v,color)
			temp_markup[u][v]=k
			k+=1
		
		goban.display(temp_grid,temp_markup)
		
		self.comment_box2.delete(1.0, END)
		if comment:
			self.comment_box2.insert(END,comment)
		u=i+goban.mesh[i][j][0]
		v=j+goban.mesh[i][j][1]
		local_area=goban.draw_point(u,v,1,color="",outline="")
		goban.tag_bind(local_area, "<Leave>", lambda e: self.leave_variation(goban,grid,markup))
		
		self.current_variation_goban=goban
		self.current_variation_grid=grid
		self.current_variation_markup=markup
		self.current_variation_i=i
		self.current_variation_j=j
		self.current_variation_move=move
		self.current_variation_sequence=sequence
		
		self.bind("<Up>", self.show_variation_next)
		self.bind("<Down>", self.show_variation_prev)
		self.bind("<MouseWheel>", self.mouse_wheel)
		if not self.inverted_mouse_wheel:
			goban.tag_bind(local_area,"<Button-4>", self.show_variation_next)
			goban.tag_bind(local_area,"<Button-5>", self.show_variation_prev)
		else:
			goban.tag_bind(local_area,"<Button-5>", self.show_variation_next)
			goban.tag_bind(local_area,"<Button-4>", self.show_variation_prev)
		self.set_status(_("Use mouse wheel or keyboard up/down keys to display the sequence move by move."))
	
	def mouse_wheel(self,event):
		if self.current_variation_sequence==None:
			return
		d = event.delta
		if self.inverted_mouse_wheel:
			d*=-1
		if d>0:
			self.show_variation_next()
		elif d<0:
			self.show_variation_prev()
	
	def show_variation_next(self,event=None):
		if self.current_variation_sequence==None:
			return
		move=(self.current_variation_move+1)%(len(self.current_variation_sequence)+1)
		move=max(1,move)
		#log(move,'/',len(self.current_variation_sequence))
		self.show_variation_move(self.current_variation_goban,self.current_variation_grid,self.current_variation_markup,self.current_variation_i,self.current_variation_j,move)
	
	def show_variation_prev(self,event=None):
		if self.current_variation_sequence==None:
			return
		move=(self.current_variation_move-1)%len(self.current_variation_sequence)
		if move<1:
			move=len(self.current_variation_sequence)
		
		self.show_variation_move(self.current_variation_goban,self.current_variation_grid,self.current_variation_markup,self.current_variation_i,self.current_variation_j,move)

	def show_territories(self,event=None):
		black_t=self.territories[0]
		white_t=self.territories[1]
		
		dim=self.dim
		markup=[["" for row in range(dim)] for col in range(dim)]
		
		for i,j in black_t:
			markup[i][j]=-1
		
		for i,j in white_t:
			markup[i][j]=-2
		
		self.goban1.display(self.current_grid,markup)
	
	def prepare_data_for_chart(self):
		data=[]
		for m in range(0,self.nb_moves+1):
			one_data={}
			data.append(one_data)
			one_move=get_node(self.gameroot,m)

			try:
				player_color,player_move=one_move.get_move()
				one_data['player_color']=player_color.lower() #which turn it is to play
			except:
				pass
			
			try:
				player_move=ij2gtp(player_move)
				one_data['move']=m #move number
			except:
				pass
			
			try:
				es=one_move.get('ES')
				if es[0]=="B":	
					one_data['score_estimation']=float(es[1:])
				else:
					one_data['score_estimation']=-float(es[1:])
				
				one_data['lower_bound_score']=one_data['score_estimation']
				one_data['upper_bound_score']=one_data['score_estimation']
				
			except:
				pass
			
			try:
				ubs=one_move.get('UBS')
				if ubs[0]=="B":	
					one_data['upper_bound_score']=float(ubs[1:])
				else:
					one_data['upper_bound_score']=-float(ubs[1:])
			except:
				pass
			
			try:
				lbs=one_move.get('LBS')
				if lbs[0]=="B":	
					one_data['lower_bound_score']=float(lbs[1:])
				else:
					one_data['lower_bound_score']=-float(lbs[1:])
			except:
				pass
			
			try:
				winrate=one_move.get('MCWR')
				if player_color in ('b',"B"):
					one_data['monte_carlo_win_rate']=float(winrate.split("%")[0])
				else:
					one_data['monte_carlo_win_rate']=float(winrate.split("/")[1][:-1])
			except:
				pass
			
			try:
				winrate=one_move.get('VNWR')
				if player_color in ('b',"B"):
					one_data['value_network_win_rate']=float(winrate.split("%")[0])
				else:
					one_data['value_network_win_rate']=float(winrate.split("/")[1][:-1])
			except:
				pass
			
			#position win rate is the win rate for the position right before the player plays his move
			#so it is the win rate of the best move by the computer for this position
			#because we consider the bot plays perfectly
			try:
				winrate=one_move.get('BWWR')
				if player_color in ('w',"W"):
					current_position_win_rate=float(winrate.split("/")[1][:-1])
				else:
					current_position_win_rate=float(winrate.split("%")[0])
				one_data['position_win_rate']=current_position_win_rate
			except:
				pass
			
			#delta is the [position win rate of the next move] - [position win rate of the current move]
			#so it allows to compare how the game would evolve from that position:
			# 1/ in the case the computer best move is played (current_position_win_rate)
			# 2/ compared with when the actual game move was played (next_position_win_rate)
			# positive delta means the game evolves better when the actual game move is played
			# negative delta means the game evolves better when the computer move is played
			try:
				next_move=get_node(self.gameroot,m+1)
				winrate=next_move.get('BWWR')
				if player_color in ('w',"W"):
					next_position_win_rate=float(winrate.split("/")[1][:-1])
				else:
					next_position_win_rate=float(winrate.split("%")[0])
				computer_move=one_move.get('CBM')
				if player_move==computer_move:
					# in case the computer best move is the actual game move then:
					# 1/ normally delta=0
					# 2/ let's update current_position_win_rate using next_position_win_rate because it is a better evaluation
					current_position_win_rate=next_position_win_rate
					one_data['position_win_rate']=next_position_win_rate
				delta=next_position_win_rate-one_data['position_win_rate'] #this will fail if the calculation of current_position_win_rate above failed, this is what we want
				one_data['winrate_delta']=delta

			except:
				pass
			
			#delta for monte carlo win rate
			try:
				next_move=get_node(self.gameroot,m+1)
				winrate=next_move.get('MCWR')
				if player_color in ('w',"W"):
					next_position_win_rate=float(winrate.split("/")[1][:-1])
				else:
					next_position_win_rate=float(winrate.split("%")[0])
				computer_move=one_move.get('CBM')
				if player_move==computer_move:
					current_position_win_rate=next_position_win_rate
					one_data['monte_carlo_win_rate']=next_position_win_rate
				delta=next_position_win_rate-one_data['monte_carlo_win_rate']
				one_data['mcwr_delta']=delta
			except:
				pass
			
			#delta for value network win rate
			try:
				next_move=get_node(self.gameroot,m+1)
				winrate=next_move.get('VNWR')
				if player_color in ('w',"W"):
					next_position_win_rate=float(winrate.split("/")[1][:-1])
				else:
					next_position_win_rate=float(winrate.split("%")[0])
				computer_move=one_move.get('CBM')
				if player_move==computer_move:
					current_position_win_rate=next_position_win_rate
					one_data['value_network_win_rate']=next_position_win_rate
				delta=next_position_win_rate-one_data['value_network_win_rate']
				one_data['vnwr_delta']=delta
			except:
				pass
			
			if len(one_data)<=2:
				#if move number and color are the only data available for this point
				#then we don't need that data point
				data.pop()
		return data
	
	def show_graphs(self,event=None):
		new_popup=OpenChart(self,self.data_for_chart,self.nb_moves)
		new_popup.current_move=self.current_move
		self.add_popup(new_popup)
		
	
	def hide_territories(self,event=None):
		self.goban1.display(self.current_grid,self.current_markup)
	
	
	def display_move(self,move=1):
		dim=self.dim
		goban1=self.goban1
		goban2=self.goban2
		self.move_number.config(text=str(move)+'/'+str(self.nb_moves))
		log("========================")
		log("displaying move",move)
		grid1=[[0 for row in range(dim)] for col in range(dim)]
		markup1=[["" for row in range(dim)] for col in range(dim)]
		grid2=[[0 for row in range(dim)] for col in range(dim)]
		markup2=[["" for row in range(dim)] for col in range(dim)]
		board, noneed = sgf_moves.get_setup_and_moves(self.sgf)

		self.current_grid=grid1
		self.current_markup=markup1

		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				place(grid1,row,col,1)
				place(grid2,row,col,1)
			else:
				place(grid1,row,col,2)
				place(grid2,row,col,2)
		
		
		m=0
		for m in range(1,move):
			one_move=get_node(self.gameroot,m)
			if one_move==False:
				log("(2)leaving because one_move==False")
				return
			
			ij=one_move.get_move()[1]
			
			if ij==None:
				log("(3)skipping because ij==None",ij)
				continue

			
			if one_move.get_move()[0]=='b':color=1
			else:color=2
			i,j=list(ij)
			place(grid1,i,j,color)
			place(grid2,i,j,color)
			
			if len(one_move)==0:
				log("(4)leaving because len(one_move)==0")
				goban1.display(grid1,markup1)
				goban2.display(grid2,markup2)
				return
		

		
		self.territories=[[],[]]
		if m>0:
			the_move=one_move
			if one_move.has_property("TB"):
				self.territories[0]=one_move.get("TB")
			if one_move.has_property("TW"):
				self.territories[1]=one_move.get("TW")
		if self.territories!=[[],[]]:
			self.territory_button.grid()
		else:
			self.territory_button.grid_remove()
		
		#indicating last play with delta
		self.comment_box1.delete(1.0, END)
		"""if m>=0:
			if get_node(self.gameroot,m+1).has_property("C"):
				self.comment_box1.insert(END,get_node(self.gameroot,m+1).get("C"))
		"""
		
		if m>=0:
			left_comments=self.get_node_comments()
			if get_node(self.gameroot,m+1).has_property("C"):
				left_comments+="\n"+get_node(self.gameroot,m+1).get("C")
			self.comment_box1.insert(END,left_comments)
			
		if m>0:
			markup1[i][j]=0
			markup2[i][j]=0

		self.comment_box2.delete(1.0, END)
		#next sequence in current game ############################################################################
		main_sequence=[]
		for m in range(self.realgamedeepness):
			one_move=get_node(self.gameroot,move+m)
			if one_move==False:
				log("(5)leaving because one_move==False")
				break
			ij=one_move.get_move()[1]
			if ij==None:
				log("(6)skipping because ij==None",ij)
				break
			if one_move.get_move()[0]=='b':	c=1
			else: c=2
			main_sequence.append([c,ij,"A",None,"black","black"])
			if m==0:
				real_game_ij=ij
		try:
			i,j=list(get_node(self.gameroot,move).get_move()[1])
		except:
			self.prev_move()
			return
		if main_sequence:
			markup1[i][j]=main_sequence
		else:
			real_game_ij=(-1,-1)
			#real_game_ij=get_node(self.gameroot,move).get_move()[1]
		
		#alternative sequences ####################################################################################
		parent=get_node(self.gameroot,move-1)
		if parent==False:
			log("(7)leaving because one_move==False")
			return
		if len(parent)<=1:
			log("no alternative move")
			goban1.display(grid1,markup1)
			goban2.display(grid2,markup2)
			self.table_button.config(state='disabled')
			return
		else:
			self.table_button.config(state='normal')

		for a in range(1,min(len(parent),self.maxvariations+1)):
			one_alternative=parent[a]
			ij=one_alternative.get_move()[1]

			displaycolor='black'
			
			if one_alternative.get_move()[0]=='b': c=1
			else: c=2

			if one_alternative.has_property("BWWR") or one_alternative.has_property("VNWR") or one_alternative.has_property("MCWR"):
				if one_alternative.has_property("BWWR"):
					black_prob=float(one_alternative.get("BWWR").split("%")[0])
					white_prob=100-black_prob
				elif one_alternative.has_property("VNWR"):
					black_prob=float(one_alternative.get("VNWR").split("%")[0])
					white_prob=100-black_prob
				elif one_alternative.has_property("MCWR"):
					black_prob=float(one_alternative.get("MCWR").split("%")[0])
					white_prob=100-black_prob
				
				if c==1:
					if self.variation_color_mode=="blue_for_winning":
						if black_prob>=50:
							displaycolor="blue"
						else:
							displaycolor="red"
					elif self.variation_color_mode=="blue_for_best":
						if a==1:
							displaycolor="blue"
						else:
							displaycolor="red"
					elif self.variation_color_mode=="blue_for_better":
						try:
							real_game_prob=float(the_move[0][0].get("BWR")[:-1])
							if real_game_prob<black_prob:
								displaycolor="blue"
							elif real_game_prob>black_prob:
								displaycolor="red"
						except:
							pass							
				else:
					if self.variation_color_mode=="blue_for_winning":
						if black_prob>50:
							displaycolor="red"
						else:
							displaycolor="blue"
					elif self.variation_color_mode=="blue_for_best":
						if a==1:
							displaycolor="blue"
						else:
							displaycolor="red"
					elif self.variation_color_mode=="blue_for_better":
						try:
							real_game_prob=float(the_move[0][0].get("WWR")[:-1])
							if real_game_prob<white_prob:
								displaycolor="blue"
							elif real_game_prob>white_prob:
								displaycolor="red"
						except:
							pass	
			
			
			comment=''
			for sgf_property in ("BWWR","PNV","MCWR","VNWR","PLYO","EVAL","RAVE","ES"):
				if one_alternative.has_property(sgf_property):
					comment+=format_data(sgf_property,variation_data_formating,one_alternative.get(sgf_property))+"\n"
			
			if one_alternative.has_property("C"):
				comment+=one_alternative.get("C")

			
			if ij==real_game_ij:
				letter_color="black"
			else:
				letter_color=displaycolor
			
			alternative_sequence=[[c,ij,chr(64+a),comment,displaycolor,letter_color]]
			while len(one_alternative)>0:
				one_alternative=one_alternative[0]
				ij=one_alternative.get_move()[1]
				if one_alternative.get_move()[0]=='b':c=1
				else:c=2
				alternative_sequence.append([c,ij,chr(64+a),comment,"whocare?","whocare"])
			i,j=parent[a].get_move()[1]
			markup2[i][j]=alternative_sequence
			
		goban1.display(grid1,markup1)
		goban2.display(grid2,markup2)
		
	def open_move(self):
		log("Opening move",self.current_move)
		
		new_popup=OpenMove(self,self.current_move,self.dim,self.sgf,self.goban_size)
		new_popup.goban.mesh=self.goban1.mesh
		new_popup.goban.wood=self.goban1.wood
		new_popup.goban.black_stones=self.goban1.black_stones
		new_popup.goban.white_stones=self.goban1.white_stones
		new_popup.goban.no_redraw=[]
		
		new_popup.goban.display(new_popup.grid,new_popup.markup)
		
		self.add_popup(new_popup)
	
	def get_node_comments(self):
		comments=""
		if self.current_move==1:
			if self.gameroot.has_property("RSGF"):
				comments+=self.gameroot.get("RSGF")
			if self.gameroot.has_property("PB"):
				comments+=_("Black")+": "+self.gameroot.get("PB")+"\n"
			if self.gameroot.has_property("PW"):
				comments+=_("White")+": "+self.gameroot.get("PW")+"\n"
			
		comments+="\n"+_("Move %i")%self.current_move
		game_move_color,game_move=get_node(self.gameroot,self.current_move).get_move()
		
		if game_move_color.lower()=="w":
			comments+="\n"+(position_data_formating["W"])%ij2gtp(game_move)
		elif game_move_color.lower()=="b":
			comments+="\n"+(position_data_formating["B"])%ij2gtp(game_move)
		
		node=get_node(self.gameroot,self.current_move)
		if node.has_property("CBM"):
			if self.gameroot.has_property("BOT"):
				bot=self.gameroot.get("BOT")
			else:
				bot=_("the computer")
			comments+="\n"+(position_data_formating["CBM"])%(bot,node.get("CBM"))
			try:
				if node[1].has_property("BKMV"):
					if node[1].get("BKMV")=="yes":
						comments+=" ("+variation_data_formating["BKMV"]+")"
			except:
				pass
		try:
			if node.has_property("BWWR"):
				if node[0].has_property("BWWR"):
					if node.get_move()[0].lower()=="b":
						comments+="\n\n"+_("Black win probability:")
						comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("BWWR").split("/")[0]
						comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("BWWR").split("/")[0]
						comments+=" (%+.2fpp)"%(float(node[0].get("BWWR").split("%/")[0])-float(node.get("BWWR").split("%/")[0]))
					else:
						comments+="\n\n"+_("White win probability:")
						comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("BWWR").split("/")[1]
						comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("BWWR").split("/")[1]
						comments+=" (%+.2fpp)"%(float(node[0].get("BWWR").split("%/")[1][:-1])-float(node.get("BWWR").split("%/")[1][:-1]))
		except:
			pass
		
		try:
			if node.has_property("VNWR"):
				if node[0].has_property("VNWR"):
					if node.get_move()[0].lower()=="b":
						comments+="\n\n"+_("Black Value Network win probability:")
						comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("VNWR").split("/")[0]
						comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("VNWR").split("/")[0]
						comments+=" (%+.2fpp)"%(float(node[0].get("VNWR").split("%/")[0])-float(node.get("VNWR").split("%/")[0]))
					else:
						comments+="\n\n"+_("White Value Network win probability:")
						comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("VNWR").split("/")[1]
						comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("VNWR").split("/")[1]
						comments+=" (%+.2fpp)"%(float(node[0].get("VNWR").split("%/")[1][:-1])-float(node.get("VNWR").split("%/")[1][:-1]))
		except:
			pass
		
		try:
			if node.has_property("MCWR"):
				if node[0].has_property("MCWR"):
					if node.get_move()[0].lower()=="b":
						comments+="\n\n"+_("Black Monte Carlo win probability:")
						comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("MCWR").split("/")[0]
						comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("MCWR").split("/")[0]
						comments+=" (%+.2fpp)"%(float(node[0].get("MCWR").split("%/")[0])-float(node.get("MCWR").split("%/")[0]))
					else:
						comments+="\n\n"+_("White Monte Carlo win probability:")
						comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("MCWR").split("/")[1]
						comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("MCWR").split("/")[1]
						comments+=" (%+.2fpp)"%(float(node[0].get("MCWR").split("%/")[1][:-1])-float(node.get("MCWR").split("%/")[1][:-1]))
		except:
			pass
		
		return comments
	
	def open_table(self):
		log("opening table")
		
		new_popup=Toplevel(self.parent)
		Label(new_popup,text=" ").grid(row=0,column=0)
		Label(new_popup,text=" ").grid(row=1000,column=1000)

		row=1
		comments=self.get_node_comments()
		Label(new_popup,text=comments,justify=LEFT).grid(row=row,column=1,columnspan=100,sticky=W)
		
		Label(new_popup,text=" ").grid(row=row+1,column=0)
		
		columns_header=[_("Move"),'nothing here',_("Win rate"),_("Monte Carlo win rate"),_("Value Network win rate"),_("Policy Network value"),_("Playouts"),_("Evaluation"),_("RAVE"),_("Score estimation")]
		columns_sgf_properties=["nothing here","nothing here","BWWR","MCWR","VNWR","PNV","PLYO","EVAL","RAVE","ES"]
		parent=get_node(self.gameroot,self.current_move-1)
		nb_variations=min(len(parent)-1,self.maxvariations+1)
		log(nb_variations,"variations")
		
		columns=[[None for i in range(nb_variations+1)] for j in range(len(columns_header))]
		
		for a in range(1,min(len(parent),self.maxvariations+1)):
			one_alternative=parent[a]
			c=0
			for key in columns_sgf_properties:
				if one_alternative.has_property(key):
					value=one_alternative.get(key)
					if "%/" in value:
						if parent[0].get_move()[0].lower()=="b":
							value=value.split("/")[0]
						else:
							value=value.split("/")[1]
					columns[c][a]=value
				c+=1
			columns[0][a]="ABCDEFGHIJKLMNOPQRSTUVWXYZ"[a-1]
			columns[1][a]=ij2gtp(one_alternative.get_move()[1])
		
		try:
			columns[0][0]="A"
			columns[1][0]=ij2gtp(parent[0].get_move()[1])
			one_alternative=parent[0][1]
			c=0
			for key in columns_sgf_properties:
				if one_alternative.has_property(key):
					value=one_alternative.get(key)
					if "%/" in value:
						if parent[0].get_move()[0].lower()=="b":
							value=value.split("/")[0]
						else:
							value=value.split("/")[1]
					columns[c][0]=value
				c+=1
		except:
			pass
		c=0
		for column in columns:
			empty=True
			for row in column:
				if row!=None:
					empty=False
					break
			if empty:
				columns_header[c]=None
			c+=1
		
		row=10
		new_popup=Frame(new_popup,bd=2,relief=RIDGE)
		new_popup.grid(row=row,column=10)
		
		row=10
		c=0
		for header in columns_header:
			if header:
				if c==0:
					Label(new_popup,text=header,relief=RIDGE).grid(row=row,column=10+c,columnspan=2,sticky=W+E)
				elif c==1:
					pass
				else:
					Label(new_popup,text=header,relief=RIDGE).grid(row=row,column=10+c,sticky=W+E)
				Frame(new_popup,height=2,bd=1,relief=RIDGE).grid(row=row+1,column=10+c,sticky=W+E)
			c+=1
		row+=2
		
		for r in range(nb_variations):
			for c in range(len(columns)):
				if columns_header[c]:
					Label(new_popup,text=columns[c][r],relief=RIDGE).grid(row=row+r,column=10+c,sticky=W+E)
			if r==0:
				row+=1
				for c in range(len(columns)):
					if columns_header[c]:
						Frame(new_popup,height=2,bd=1,relief=RIDGE).grid(row=row+r,column=10+c,sticky=W+E)

	def update_from_file(self):
		try:
			h1=hash(open_sgf(self.filename).serialise())
			h2=hash(self.sgf.serialise())
			
			if h1!=h2:
				log("Reloding the RSGF file from hard drive")
				old_sgf=self.sgf
				self.sgf=open_sgf(self.filename)
				log("Updating data")
				#self.dim=self.sgf.get_size()
				#self.komi=self.sgf.get_komi()
				self.gameroot=self.sgf.get_root()
				nb_moves=get_node_number(self.gameroot)
				if nb_moves!=self.nb_moves:
					log("Updating label")
					self.nb_moves=nb_moves
					self.move_number.config(text=str(self.current_move)+'/'+str(self.nb_moves))
				
				new_parent=get_node(self.gameroot,self.current_move-1)
				old_parent=get_node(old_sgf.get_root(),self.current_move-1)
				if len(old_parent)!=len(new_parent):
					#current move beeing displayed should be updated
					log("updating current display")
					self.pressed=time.time()
					pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
					self.parent.after(0,lambda: pf())
				
				log("Updating data for charts")
				self.data_for_chart=self.prepare_data_for_chart()
				if not self.charts_button:
					#there was no chart up to this point
					for data in self.data_for_chart:
						if data<>None:
							log("Creating the chart button")
							self.charts_button=Button(self, text=_('Graphs'))
							self.charts_button.bind('<Button-1>', self.show_graphs)
							self.charts_button.grid(column=3,row=2,sticky=E)
							break
				
				for popup in self.popups:
					if isinstance(popup,OpenChart):
						log("Updating chart")
						popup.nb_moves=self.nb_moves
						popup.data=self.data_for_chart
						popup.initialize()
						popup.display()
		except:
			pass
		
		self.after(10000,self.update_from_file)
		
	def initialize(self):

		self.realgamedeepness=5
		try:
			self.realgamedeepness=int(Config.get("Review", "RealGameSequenceDeepness"))
		except:
			Config.set("Review", "RealGameSequenceDeepness",self.realgamedeepness)
			Config.write(open(config_file,"w"))
		
		self.maxvariations=10
		try:
			self.maxvariations=int(Config.get("Review", "MaxVariations"))
		except:
			Config.set("Review", "MaxVariations",self.maxvariations)
			Config.write(open(config_file,"w"))
		
		self.sgf = open_sgf(self.filename)

		self.dim=self.sgf.get_size()
		self.komi=self.sgf.get_komi()
		
		log("boardsize:",self.dim)
		#goban.dim=size
		
		#goban.prepare_mesh()
		self.gameroot=self.sgf.get_root()
		self.nb_moves=get_node_number(self.gameroot)
		
		for m in range(0,self.nb_moves+1)[::-1]:
			one_move=get_node(self.gameroot,m)
			player_color,player_move=one_move.get_move()
			if (player_color==None) or (player_move==None):
				self.nb_moves-=1
			else:
				break


		self.parent.title('GoReviewPartner')
		self.protocol("WM_DELETE_WINDOW", self.close)
		
		self.popups=[]
		
		bg=self.cget("background")
		#self.configure(background=bg)
		
		Label(self,text='   ',background=bg).grid(column=0,row=0)
		
		buttons_bar=Frame(self,background=bg)
		buttons_bar.grid(column=1,row=1,columnspan=3)
		
		first_move_button=Button(buttons_bar, text='|<< ',command=self.first_move)
		first_move_button.grid(column=8,row=1)
		
		prev_10_moves_button=Button(buttons_bar, text=' << ',command=self.prev_10_move)
		prev_10_moves_button.grid(column=9,row=1)
		
		prev_button=Button(buttons_bar, text=' <  ',command=self.prev_move)
		prev_button.grid(column=10,row=1)
		
		Label(buttons_bar,text='          ',background=bg).grid(column=19,row=1)
		
		self.move_number=Label(buttons_bar,text='   ',background=bg)
		self.move_number.grid(column=20,row=1)
		

		
		Label(buttons_bar,text='          ',background=bg).grid(column=29,row=1)
		
		next_button=Button(buttons_bar, text='  > ',command=self.next_move)
		next_button.grid(column=30,row=1)
		
		next_10_moves_button=Button(buttons_bar, text=' >> ',command=self.next_10_move)
		next_10_moves_button.grid(column=31,row=1)
		
		final_move_button=Button(buttons_bar, text=' >>|',command=self.final_move)
		final_move_button.grid(column=32,row=1)
		
		buttons_bar2=Frame(self,background=bg)
		buttons_bar2.grid(column=1,row=2,sticky=W)
		
		open_button=Button(buttons_bar2, text=_('Open position'),command=self.open_move)
		open_button.grid(column=1,row=1)
		
		self.territory_button=Button(buttons_bar2, text=_('Show territories'))
		self.territory_button.grid(column=2,row=1)
		self.territory_button.bind('<Button-1>', self.show_territories)
		self.territory_button.bind('<ButtonRelease-1>', self.hide_territories)
		
		self.data_for_chart=self.prepare_data_for_chart()
		self.charts_button=None
		for data in self.data_for_chart:
			if data<>None:
				self.charts_button=Button(self, text=_('Graphs'))
				self.charts_button.bind('<Button-1>', self.show_graphs)
				self.charts_button.grid(column=3,row=2,sticky=E)
				break
		
		self.parent.bind('<Left>', self.prev_move)
		self.parent.bind('<Right>', self.next_move)

		#Label(app,background=bg).grid(column=1,row=2)

		row=10

		#Label(self,background=bg).grid(column=1,row=row-1)

		#self.goban1 = Canvas(self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban1 = Goban(self.dim,master=self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		

		
		self.goban1.grid(column=1,row=row,sticky=W+E+N+S)
		Label(self, text='            ',background=bg).grid(column=2,row=row)
		#self.goban2 = Canvas(self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban2 = Goban(self.dim, master=self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban2.mesh=self.goban1.mesh
		self.goban2.wood=self.goban1.wood
		self.goban2.black_stones=self.goban1.black_stones
		self.goban2.white_stones=self.goban1.white_stones
		self.goban2.grid(column=3,row=row,sticky=W+E+N+S)
		
		self.grid_rowconfigure(row, weight=1)
		self.grid_columnconfigure(1, weight=1)
		self.grid_columnconfigure(3, weight=1)
		
		self.goban1.space=self.goban_size/(self.dim+1+1)
		self.goban2.space=self.goban_size/(self.dim+1+1)
		
		self.bind('<Control-q>', self.save_left_as_png)
		self.bind('<Control-w>', self.save_right_as_png)
		
		Label(self,text='   ',background=bg).grid(column=4,row=row+1)
		
		police = tkFont.nametofont("TkFixedFont")
		lpix = police.measure("a")
		self.lpix=lpix
		self.comment_box1=ScrolledText(self,font=police,wrap="word",width=int(self.goban_size/lpix-2),height=5,foreground='black')
		self.comment_box1.grid(column=1,row=row+4)
		
		self.table_button=Button(self,text=_("Table"),command=self.open_table)
		self.table_button.grid(column=2,row=row+4)
		
		self.comment_box2=ScrolledText(self,font=police,wrap="word",width=int(self.goban_size/lpix-2),height=5,foreground='black')
		self.comment_box2.grid(column=3,row=row+4)
		
		self.status_bar=Label(self,text='',background=bg)
		self.status_bar.grid(column=1,row=row+5,sticky=W,columnspan=3)
		
		#Label(self,text='   ',background=bg).grid(column=4,row=row+6)
		
		goban.show_variation=self.show_variation
		
		self.goban1.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+Q> to save the goban as an image.")))
		self.goban2.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+W> to save the goban as an image.")))
		
		first_move_button.bind("<Enter>",lambda e: self.set_status(_("Go to first move.")))
		prev_10_moves_button.bind("<Enter>",lambda e: self.set_status(_("Go back 10 moves.")))
		prev_button.bind("<Enter>",lambda e: self.set_status(_("Go back one move. Shortcut: keyboard left key.")))
		open_button.bind("<Enter>",lambda e: self.set_status(_("Open this position onto a third goban to play out variations.")))
		next_button.bind("<Enter>",lambda e: self.set_status(_("Go forward one move. Shortcut: keyboard right key.")))
		next_10_moves_button.bind("<Enter>",lambda e: self.set_status(_("Go forward 10 moves.")))
		final_move_button.bind("<Enter>",lambda e: self.set_status(_("Go to final move.")))
		self.territory_button.bind("<Enter>",lambda e: self.set_status(_("Keep pressed to show territories.")))
		for button in [first_move_button,prev_10_moves_button,prev_button,open_button,next_button,next_10_moves_button,final_move_button,self.territory_button,self.goban1,self.goban2]:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		self.goban1.bind("<Configure>",self.redraw)
		self.after(10000,self.update_from_file)
	
	def redraw(self, event):
		new_size=min(event.width,event.height)
		new_space=new_size/(self.dim+1+1)
		self.goban1.space=new_space
		self.goban2.space=new_space
		
		new_anchor_x=(event.width-new_size)/2
		self.goban1.anchor_x=new_anchor_x
		self.goban2.anchor_x=new_anchor_x
		
		new_anchor_y=(event.height-new_size)/2
		self.goban1.anchor_y=new_anchor_y
		self.goban2.anchor_y=new_anchor_y
		
		self.goban1.redraw()
		self.goban2.redraw()
		
		if sys.platform!="darwin":
			#https://github.com/pnprog/goreviewpartner/issues/7
			self.comment_box1.config(width=int(event.width/self.lpix-10))
			self.comment_box2.config(width=int(event.width/self.lpix-10))

	def set_status(self,msg):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")

	def save_left_as_png(self,e=None):
		filename = save_png_file(parent=self,filename='move'+str(self.current_move)+'.png')
		canvas2png(self.goban1,filename)

	def save_right_as_png(self,e=None):
		filename = save_png_file(parent=self,filename='move'+str(self.current_move)+'.png')
		canvas2png(self.goban2,filename)
	
from gomill import sgf, sgf_moves
import goban
#goban.fuzzy=float(Config.get("Review", "FuzzyStonePlacement"))

if __name__ == "__main__":
	Config = ConfigParser.ConfigParser()
	Config.read(config_file)
	if len(sys.argv)==1:
		temp_root = Tk()
		filename = open_rsgf_file(parent=temp_root)
		temp_root.destroy()
		log(filename)
		if not filename:
			sys.exit()
	else:
		filename=sys.argv[1]
	top = Application()
	display_factor=.5
	try:
		display_factor=float(Config.get("Review", "GobanScreenRatio"))
	except:
		Config.set("Review", "GobanScreenRatio",display_factor)
		Config.write(open(config_file,"w"))
	screen_width = top.winfo_screenwidth()
	screen_height = top.winfo_screenheight()
	width=int(display_factor*screen_width)
	height=int(display_factor*screen_height)
	popup=DualView(top,filename,min(width,height))
	top.add_popup(popup)
	top.mainloop()
